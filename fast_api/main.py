#!/usr/bin/env python3
"""
Simple FastAPI server for F5-TTS Vietnamese inference
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Request, Depends
import subprocess
from pathlib import Path
from datetime import datetime
import os
import io
import time
import json
import re
import asyncio
from typing import AsyncGenerator
from middleware.rate_limiter_redis import RedisRateLimiter
from config import (
    VOICES,
    BASE_DIR,
    REF_AUDIO_DIR,
    OUTPUT_DIR,
    STATIC_DIR,
    SAMPLES_DIR,
    VOCAB_FILE,
    CHECKPOINT_FILE,
    API_TITLE,
    API_VERSION,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    HF_HOME,
    HF_HUB_CACHE,
    MODEL_NAME,
    VOCODER_NAME,
    MIN_TEXT_LENGTH,
    MAX_TEXT_LENGTH,
    MIN_SPEED,
    MAX_SPEED,
    MIN_CFG_STRENGTH,
    MAX_CFG_STRENGTH,
    RATE_LIMIT_REQUESTS
)

rate_limiter = RedisRateLimiter()

async def get_session_id(request: Request):
    return rate_limiter.get_session_id(request)

app = FastAPI(title=API_TITLE, version=API_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Set HuggingFace cache
os.environ["HF_HOME"] = HF_HOME
os.environ["HF_HUB_CACHE"] = HF_HUB_CACHE


class TTSRequest(BaseModel):
    voice: str = "tran_ha_linh"
    text: str
    speed: float = 1.0
    output_file: str = "output.wav"


@app.get("/")
def read_root():
    """Serve the frontend at root path."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    # Fallback: redirect to static path
    return RedirectResponse(url="/static/index.html")


@app.get("/healthz")
def health_check():
    """Health check endpoint for frontend status monitoring"""
    return {
        "status": "ok",
        "service": API_TITLE,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": API_VERSION
    }



@app.get("/voices")
def get_voices():
    """Get all available voices with metadata"""
    try:
        voices_list = []
        for voice_id, voice_data in VOICES.items():
            voice_info = {
                "id": voice_id,
                "name": voice_data.get("name", voice_id.replace("_", " ").title()),
                "description": voice_data.get("description", ""),
                "language": voice_data.get("language", "vi"),
                "gender": voice_data.get("gender", "unknown"),
                "thumbnail": voice_data.get("thumbnail", "/static/thumbnails/default.jpg"),
                "sample_audio": voice_data.get("sample_audio", ""),
                "created_at": "2025-01-01T00:00:00Z"
            }
            voices_list.append(voice_info)
        
        return {
            "voices": voices_list,
            "total": len(voices_list)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load voice configurations: {str(e)}"
        )


@app.get("/voices/{voice_id}")
def get_voice_detail(voice_id: str):
    """Get detailed information about a specific voice"""
    if voice_id not in VOICES:
        raise HTTPException(
            status_code=404,
            detail=f"Voice '{voice_id}' not found"
        )
    
    voice_data = VOICES[voice_id]
    ref_audio_path = REF_AUDIO_DIR / voice_data["audio"]
    
    return {
        "id": voice_id,
        "name": voice_data.get("name", voice_id.replace("_", " ").title()),
        "description": voice_data.get("description", ""),
        "language": voice_data.get("language", "vi"),
        "gender": voice_data.get("gender", "unknown"),
        "thumbnail": voice_data.get("thumbnail", "/static/thumbnails/default.jpg"),
        "sample_audio": voice_data.get("sample_audio", ""),
        "ref_text": voice_data.get("ref_text", ""),
        "duration": 0.0,  # TODO: Calculate from audio file
        "sample_rate": 24000,
        "created_at": "2025-01-01T00:00:00Z",
        "stats": {
            "total_generations": 0,
            "avg_generation_time": 0.0
        }
    }


@app.post("/synthesize")
def synthesize(request: TTSRequest, session_id: str = Depends(get_session_id)):
    """
    Synthesize speech from text
    
    Example:
    {
        "voice": "tran_ha_linh",
        "text": "xin chào các bạn",
        "speed": 1.0,
        "output_file": "output.wav"
    }
    """
    # Rate limit for anonymous sessions
    rate_info = rate_limiter.check(session_id, len(request.text))

    # Validate voice
    if request.voice not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{request.voice}' not found. Available: {list(VOICES.keys())}"
        )
    
    # Get voice config
    voice_config = VOICES[request.voice]
    ref_audio = REF_AUDIO_DIR / voice_config["audio"]
    
    # Check if reference audio exists
    if not ref_audio.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Reference audio not found: {ref_audio}"
        )
    
    # Prepare output
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / request.output_file
    
    # Build command
    command = [
        "f5-tts_infer-cli",
        "--model", MODEL_NAME,
        "--ref_audio", str(ref_audio),
        "--ref_text", voice_config["ref_text"],
        "--gen_text", request.text,
        "--speed", str(request.speed),
        "--vocoder_name", VOCODER_NAME,
        "--vocab_file", str(VOCAB_FILE),
        "--ckpt_file", str(CHECKPOINT_FILE),
        "--output_dir", str(OUTPUT_DIR),
        "--output_file", request.output_file
    ]
    
    try:
        # Run inference
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        
        response = {
            "status": "success",
            "voice": request.voice,
            "text": request.text,
            "output_file": str(output_path),
            "message": "Speech synthesized successfully"
        }
        headers = {
            "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": rate_info["reset_iso"]
        }
        return JSONResponse(content=response, headers=headers)
        
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inference failed: {e.stderr}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.get("/tts/generate-audio")
async def tts_generate_audio(
    text: str = Query(...),
    voice_id: str = Query(...),
    speed: float = Query(1.0),
    remove_silence: bool = Query(False),
    cfg_strength: float = Query(2.0),
    nfe_step: int = Query(32),
    session_id: str = Depends(get_session_id)
):
    """
    Generate speech with Server-Sent Events (SSE) for real-time progress updates.
    """
    # Validate inputs (same as tts_generate)
    if not text or len(text) < MIN_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(status_code=400, detail=f"Text length must be between {MIN_TEXT_LENGTH} and {MAX_TEXT_LENGTH} characters")
    if voice_id not in VOICES:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    if not (MIN_SPEED <= speed <= MAX_SPEED):
        raise HTTPException(status_code=400, detail=f"Speed must be between {MIN_SPEED} and {MAX_SPEED}")
    if not (MIN_CFG_STRENGTH <= cfg_strength <= MAX_CFG_STRENGTH):
        raise HTTPException(status_code=400, detail=f"cfg_strength must be between {MIN_CFG_STRENGTH} and {MAX_CFG_STRENGTH}")
    
    # Apply Redis-backed rate limiting
    rate_info = rate_limiter.check(session_id, len(text))
    
    voice_config = VOICES[voice_id]
    ref_audio_path = REF_AUDIO_DIR / voice_config["audio"]
    
    if not ref_audio_path.exists():
        raise HTTPException(status_code=500, detail=f"Reference audio not found: {ref_audio_path}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = f"output_{int(time.time())}.wav"
    output_path = OUTPUT_DIR / output_file
    
    command = [
        "f5-tts_infer-cli",
        "--model", MODEL_NAME,
        "--ref_audio", str(ref_audio_path),
        "--ref_text", voice_config["ref_text"],
        "--gen_text", text,
        "--speed", str(speed),
        "--vocoder_name", VOCODER_NAME,
        "--vocab_file", str(VOCAB_FILE),
        "--ckpt_file", str(CHECKPOINT_FILE),
        "--output_dir", str(OUTPUT_DIR),
        "--output_file", output_file
    ]
    
    if remove_silence:
        command.append("--remove_silence")
    
    async def generate_progress() -> AsyncGenerator[str, None]:
        """Stream progress updates via SSE"""
        try:
            # Send initial progress
            yield f"data: {json.dumps({'progress': 0, 'status_key': 'initializing'})}\n\n"
            
            # Start subprocess
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            progress = 0
            batch_count = 0
            total_batches = 0
            
            # Read output line by line
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                    
                line_text = line.decode('utf-8', errors='ignore').strip()
                print(line_text)  # Log to terminal
                
                # Parse progress from output
                # Look for "gen_text" lines
                if 'gen_text' in line_text:
                    progress = min(progress + 5, 30)
                    yield f"data: {json.dumps({'progress': progress, 'status_key': 'processingText'})}\n\n"
                
                # Look for batch progress "X/Y"
                batch_match = re.search(r'(\d+)/(\d+)\s+\[', line_text)
                if batch_match:
                    current = int(batch_match.group(1))
                    total = int(batch_match.group(2))
                    total_batches = total
                    batch_count = current
                    # Map batch progress to 30-90%
                    progress = 30 + int((current / total) * 60)
                    yield f"data: {json.dumps({'progress': progress, 'status_key': 'generatingAudio', 'current': current, 'total': total})}\n\n"
                
                # Look for percentage in progress bar
                percent_match = re.search(r'(\d+)%', line_text)
                if percent_match and batch_count > 0:
                    batch_progress = int(percent_match.group(1))
                    # Calculate overall progress
                    base_progress = 30 + int(((batch_count - 1) / total_batches) * 60)
                    progress = base_progress + int((batch_progress / 100) * (60 / total_batches))
                    progress = min(progress, 90)
                    yield f"data: {json.dumps({'progress': progress, 'status_key': 'generatingResult', 'current': batch_count, 'total': total_batches})}\n\n"
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode != 0:
                yield f"data: {json.dumps({'progress': 0, 'status_key': 'error', 'error_key': 'generationFailed'})}\n\n"
                return
            
            # Check if output file exists
            if output_path.exists():
                yield f"data: {json.dumps({'progress': 95, 'status_key': 'finalizingResult'})}\n\n"
                await asyncio.sleep(0.2)
                
                # Read audio file
                with open(output_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                
                file_size = len(audio_data)
                audio_duration = file_size / (24000 * 1 * 2)
                
                # Send completion with audio data URL
                import base64
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
                result_data = {
                    'progress': 100,
                    'status_key': 'complete',
                    'audio_data': audio_b64,
                    'filename': output_file,
                    'duration': audio_duration,
                    'file_size': file_size
                }
                yield f"data: {json.dumps(result_data)}\n\n"
            else:
                yield f"data: {json.dumps({'progress': 0, 'status_key': 'error', 'error_key': 'outputFileNotCreated'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'progress': 0, 'status_key': 'error', 'error': str(e)})}\n\n"
    
    headers = {
        "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
        "X-RateLimit-Remaining": str(rate_info["remaining"]),
        "X-RateLimit-Reset": rate_info["reset_iso"]
    }
    return StreamingResponse(generate_progress(), media_type="text/event-stream", headers=headers)


# Mount static files for frontend
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "fast_api/static")), name="static")

# Utility: Sync reference .wav files into static samples directory
def sync_samples() -> list[dict]:
    try:
        SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        samples = []
        # Find all wav files under original_voice_ref/<voice>/*.wav
        for voice_dir in sorted(REF_AUDIO_DIR.glob("*/")):
            voice_id = voice_dir.name
            wav_files = list(voice_dir.glob("*.wav"))
            for wav in wav_files:
                target = SAMPLES_DIR / f"{voice_id}_{wav.name}"
                # Copy if not exists or source newer
                if (not target.exists()) or (wav.stat().st_mtime > target.stat().st_mtime):
                    try:
                        import shutil
                        shutil.copy2(wav, target)
                    except Exception:
                        pass
                samples.append({
                    "voice": voice_id,
                    "filename": wav.name,
                    "path": f"/static/samples/{voice_id}_{wav.name}"
                })
        return samples
    except Exception:
        return []

# Sync on startup
_SAMPLES_CACHE = sync_samples()

@app.get("/samples")
def list_samples():
    """List available sample .wav files copied to static/samples."""
    try:
        # Refresh cache each request to pick up new files
        samples = sync_samples()
        # Provide concise metadata
        items = []
        for s in samples:
            items.append({
                "id": f"{s['voice']}::{s['filename']}",
                "voice": s["voice"],
                "filename": s["filename"],
                "url": s["path"]
            })
        return {"samples": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list samples: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
