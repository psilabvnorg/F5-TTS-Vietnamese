"""
TTS synthesis endpoints
"""

import asyncio
import tempfile
import json
import shutil
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import io
import sys

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
import soundfile as sf
import numpy as np

from app.models.tts import TTSRequest, TTSProgress
from app.api.deps import ModelHandlerDep
from app.core.config import settings
from app.core.logging import logger
from app.core.voices import VOICES


router = APIRouter()


# Queue management
class QueueManager:
    """Simple queue metrics tracker"""
    def __init__(self):
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.in_queue = 0
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCE)


queue_manager = QueueManager()


@router.post("/synthesize", response_class=StreamingResponse)
async def synthesize_speech(
    request: TTSRequest,
    handler: ModelHandlerDep
):
    """
    Generate speech from text and return audio file
    
    - **text**: Text to synthesize (1-5000 characters)
    - **voice**: Voice ID to use
    - **speed**: Speech speed (0.5-2.0)
    - **remove_silence**: Remove silence from output
    
    Returns audio/wav file
    """
    # Validate voice exists (will be done by handler)
    # Check queue size
    if queue_manager.in_queue >= settings.MAX_QUEUE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Queue full ({queue_manager.in_queue}/{settings.MAX_QUEUE_SIZE}). Please try again later."
        )
    
    queue_manager.total_requests += 1
    
    # Acquire semaphore for inference
    async with queue_manager.semaphore:
        queue_manager.in_queue += 1
        
        try:
            # Create temporary output file
            output_file = tempfile.mktemp(suffix=".wav", dir=str(settings.OUTPUT_DIR))
            
            logger.info(f"Synthesizing: voice={request.voice}, text_len={len(request.text)}, speed={request.speed}")
            
            # Run inference in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            output_path, sample_rate = await loop.run_in_executor(
                None,
                handler.infer,
                request.voice,  # This will be converted to ref_audio path by handler
                "",  # ref_text - will be loaded from voice config
                request.text,  # gen_text
                output_file,  # output_path
                None,  # voices dict
                False,  # save_chunks
                request.remove_silence,
                None,  # target_rms
                None,  # cross_fade_duration
                request.nfe_step,
                request.cfg_strength,
                request.sway_sampling_coef,
                request.speed,
                None,  # fix_duration
            )
            
            # Read audio file
            audio_data, sr = sf.read(output_path)
            
            # Convert to bytes
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, sr, format="wav")
            buffer.seek(0)
            
            # Clean up temp file
            Path(output_path).unlink(missing_ok=True)
            
            queue_manager.completed_requests += 1
            logger.info(f"Synthesis complete: voice={request.voice}, sample_rate={sample_rate}")
            
            return StreamingResponse(
                buffer,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f'attachment; filename="tts_output_{request.voice}.wav"',
                    "X-Voice-ID": request.voice,
                    "X-Sample-Rate": str(sample_rate),
                }
            )
            
        except ValueError as e:
            # Voice not found or validation error
            queue_manager.failed_requests += 1
            logger.error(f"Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            ) from e
            
        except Exception as e:
            queue_manager.failed_requests += 1
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Synthesis failed: {str(e)}"
            ) from e
            
        finally:
            queue_manager.in_queue -= 1


@router.get("/generate-audio")
async def generate_audio_sse(
    text: str,
    voice_id: str,
    speed: float = 1.0,
    cfg_strength: float = 2.0,
    nfe_step: int = 32,
    remove_silence: bool = False,
    handler: ModelHandlerDep = None
):
    """
    Generate speech with Server-Sent Events (SSE) progress updates
    
    Returns event stream with progress updates and final audio file path
    """
    async def generate_progress():
        try:
            # Validate text is not empty
            if not text or text.strip() == "":
                yield f"data: {json.dumps({'error': 'Text cannot be empty'})}\n\n"
                return
            
            # Validate voice_id
            if voice_id not in VOICES:
                yield f"data: {json.dumps({'error': f'Voice ID {voice_id} not found'})}\n\n"
                return
            
            # Get voice configuration
            voice_config = VOICES[voice_id]
            ref_audio_path = str(settings.REF_AUDIO_DIR / voice_config["audio"])
            ref_text = voice_config["ref_text"]
            
            # Send progress updates
            yield f"data: {json.dumps({'progress': 10, 'status': 'Starting synthesis...'})}\n\n"
            await asyncio.sleep(0.1)
            
            yield f"data: {json.dumps({'progress': 30, 'status': 'Processing text...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Create output file
            output_file = tempfile.mktemp(suffix=".wav", dir=str(settings.OUTPUT_DIR))
            
            yield f"data: {json.dumps({'progress': 50, 'status': 'Generating audio...'})}\n\n"
            
            # Run inference
            loop = asyncio.get_event_loop()
            output_path, sample_rate = await loop.run_in_executor(
                None,
                handler.infer,
                ref_audio_path,
                ref_text,
                text,
                output_file,
                None,
                False,
                remove_silence,
                None, None,
                nfe_step,
                cfg_strength,
                None,
                speed,
                None
            )
            
            yield f"data: {json.dumps({'progress': 90, 'status': 'Finalizing...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Copy to output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{voice_id}_{timestamp}.wav"
            output_dir = settings.OUTPUT_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            final_output_path = output_dir / filename
            
            # Copy file
            shutil.copy2(output_path, final_output_path)
            
            # Get file size and duration
            audio_data, sr = sf.read(str(final_output_path))
            duration = len(audio_data) / sr
            file_size = os.path.getsize(str(final_output_path))
            
            # Build audio URL (relative path from project root)
            audio_url = f"/output/{filename}"
            
            # Success response
            success_data = {
                'progress': 100,
                'status': 'Complete!',
                'audio_url': audio_url,
                'filename': filename,
                'duration': duration,
                'file_size': file_size
            }
            yield f"data: {json.dumps(success_data)}\n\n"
            
        except Exception as e:
            logger.error(f"SSE synthesis failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_progress(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/queue")
async def get_queue_status():
    """
    Get current queue status and metrics
    """
    return {
        "current_size": queue_manager.in_queue,
        "max_size": settings.MAX_QUEUE_SIZE,
        "total_requests": queue_manager.total_requests,
        "completed": queue_manager.completed_requests,
        "failed": queue_manager.failed_requests,
        "success_rate": (
            queue_manager.completed_requests / queue_manager.total_requests * 100
            if queue_manager.total_requests > 0
            else 0.0
        )
    }
