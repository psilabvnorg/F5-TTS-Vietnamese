#!/usr/bin/env python3
"""
Simple FastAPI server for F5-TTS Vietnamese inference
Optimized with preloaded model and AsyncIO queue for concurrent users
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Request, Depends
from pathlib import Path
from datetime import datetime
import os
import io
import time
import json
import base64
import asyncio
from typing import AsyncGenerator, Tuple
import torch
import torchaudio
import numpy as np
# from middleware.rate_limiter_redis import RedisRateLimiter  # Temporarily disabled
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

# F5-TTS imports
from f5_tts.model import DiT
from f5_tts.infer.utils_infer import (
    load_vocoder,
    load_model,
    preprocess_ref_audio_text,
    infer_process,
    remove_silence_for_generated_wav
)

# rate_limiter = RedisRateLimiter()  # Temporarily disabled

# async def get_session_id(request: Request):
#     # return rate_limiter.get_session_id(request)  # Temporarily disabled
#     return "default_session"  # Placeholder when rate limiting is disabled

# Set HuggingFace cache BEFORE loading models
os.environ["HF_HOME"] = HF_HOME
os.environ["HF_HUB_CACHE"] = HF_HUB_CACHE

# ============================================
# STEP 2: PRELOAD MODEL AND VOCODER AT STARTUP
# ============================================
print("🔄 Loading F5-TTS model...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"📍 Using device: {device}")

# Model configuration
model_cfg = dict(
    dim=1024,
    depth=22,
    heads=16,
    ff_mult=2,
    text_dim=512,
    conv_layers=4
)

# Load model (once at startup)
F5TTS_model = load_model(
    model_cls=DiT,
    model_cfg=model_cfg,
    ckpt_path=str(CHECKPOINT_FILE),
    mel_spec_type=VOCODER_NAME,
    vocab_file=str(VOCAB_FILE)
)
print(f"✅ Model loaded successfully on {device}")

# Load vocoder (once at startup)
vocoder = load_vocoder(vocoder_name=VOCODER_NAME, is_local=False, device=device)
print(f"✅ Vocoder '{VOCODER_NAME}' loaded successfully")

# ============================================
# STEP 2.5: PRELOAD REFERENCE AUDIOS AT STARTUP
# ============================================
def preload_reference_audios():
    """
    Preload and cache all reference audios at startup.
    This eliminates the 0.5-1s delay per voice on first request.
    """
    print("\n🔄 Preloading reference audios...")
    loaded_count = 0
    failed_count = 0
    
    for voice_id, voice_config in VOICES.items():
        try:
            # Construct reference audio path
            ref_audio_path = REF_AUDIO_DIR / voice_config["audio"]
            
            if not ref_audio_path.exists():
                print(f"⚠️  Warning: Reference audio not found for '{voice_id}': {ref_audio_path}")
                failed_count += 1
                continue
            
            # Preprocess reference audio
            ref_audio, ref_text = preprocess_ref_audio_text(
                ref_audio_orig=str(ref_audio_path),
                ref_text=voice_config["ref_text"]
            )
            
            # Store in cache
            ref_audio_cache[voice_id] = (ref_audio, ref_text)
            loaded_count += 1
            print(f"✅ Cached: {voice_id} ({voice_config.get('name', voice_id)})")
            
        except Exception as e:
            print(f"❌ Failed to load '{voice_id}': {str(e)}")
            failed_count += 1
    
    print(f"\n✅ Preloading complete: {loaded_count} voices loaded, {failed_count} failed")
    if loaded_count == 0:
        print("⚠️  WARNING: No reference audios were loaded! Check your voice configurations.")
    
    return loaded_count, failed_count

# Cache for preprocessed reference audios
ref_audio_cache = {}

# Preload all reference audios at startup
preload_reference_audios()

# ============================================
# STEP 3: ASYNC QUEUE AND CACHING
# ============================================
# Concurrency control - only 1 inference at a time
inference_semaphore = asyncio.Semaphore(1)

# Queue capacity
MAX_QUEUE_SIZE = 50

# Metrics tracking
class QueueMetrics:
    def __init__(self):
        self.total_requests = 0
        self.completed_requests = 0
        self.failed_requests = 0
        self.start_time = time.time()
    
    @property
    def in_queue(self):
        return self.total_requests - self.completed_requests - self.failed_requests
    
    @property
    def uptime(self):
        return time.time() - self.start_time

metrics = QueueMetrics()

def get_cached_ref_audio(voice_id: str) -> Tuple:
    """
    Get preprocessed reference audio from cache.
    All audios are preloaded at startup, so this is just a simple lookup.
    
    Args:
        voice_id: The voice identifier
        
    Returns:
        Tuple of (ref_audio, ref_text)
        
    Raises:
        ValueError: If voice_id is not found in cache
    """
    if voice_id not in ref_audio_cache:
        # This should never happen if preloading worked correctly
        available_voices = list(ref_audio_cache.keys())
        raise ValueError(
            f"Voice '{voice_id}' not found in cache. "
            f"Available voices: {available_voices}. "
            f"This may indicate the reference audio failed to load at startup."
        )
    
    return ref_audio_cache[voice_id]

# ============================================
# STEP 4: INFERENCE FUNCTION WITH QUEUE
# ============================================
async def run_inference(text: str, voice_id: str, speed: float, remove_silence: bool = False) -> Tuple:
    """
    Run inference with concurrency control
    Only 1 request processes at a time, others wait in queue
    """
    metrics.total_requests += 1
    
    async with inference_semaphore:  # Wait for available slot
        try:
            # Get cached reference audio
            ref_audio, ref_text = get_cached_ref_audio(voice_id)
            
            # Run inference in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            generated_audio, sample_rate, remove_silence_flag = await loop.run_in_executor(
                None,
                _sync_inference,
                ref_audio,
                ref_text,
                text,
                speed,
                remove_silence
            )
            
            metrics.completed_requests += 1
            return generated_audio, sample_rate, remove_silence_flag
            
        except Exception as e:
            metrics.failed_requests += 1
            raise e

def _sync_inference(ref_audio, ref_text, text, speed, remove_silence_flag):
    """Synchronous inference function to run in executor"""
    # Call infer_process matching CLI parameters
    generated_audio, sample_rate, _ = infer_process(
        ref_audio,
        ref_text,
        text,
        F5TTS_model,
        vocoder,
        mel_spec_type=VOCODER_NAME,
        speed=speed
    )
    
    # Convert numpy array to torch tensor and ensure 2D shape (channels, samples)
    if isinstance(generated_audio, np.ndarray):
        generated_audio = torch.from_numpy(generated_audio)
    
    if generated_audio.dim() == 1:
        generated_audio = generated_audio.unsqueeze(0)
    
    # Note: remove_silence in CLI works on saved files, we'll handle it after saving
    return generated_audio, sample_rate, remove_silence_flag

# ============================================
# FastAPI App
# ============================================
app = FastAPI(title=API_TITLE, version=API_VERSION)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)


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
        "version": API_VERSION,
        "model": {
            "loaded": F5TTS_model is not None and vocoder is not None,
            "device": str(device),
            "name": MODEL_NAME,
            "vocoder": VOCODER_NAME
        },
        "cache": {
            "ref_audios_loaded": len(ref_audio_cache),
            "total_voices_configured": len(VOICES),
            "cached_voices": sorted(list(ref_audio_cache.keys())),
            "preload_success_rate": f"{len(ref_audio_cache)}/{len(VOICES)}"
        },
        "queue": {
            "current_size": metrics.in_queue,
            "max_size": MAX_QUEUE_SIZE,
            "total_requests": metrics.total_requests,
            "completed": metrics.completed_requests,
            "failed": metrics.failed_requests
        },
        "capacity": {
            "max_concurrent": 1,
            "available": 1 - metrics.in_queue
        },
        "uptime_seconds": round(metrics.uptime, 2)
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
async def synthesize(request: TTSRequest):
    """
    Synthesize speech from text using preloaded model
    
    Example:
    {
        "voice": "tran_ha_linh",
        "text": "xin chào các bạn",
        "speed": 1.0,
        "output_file": "output.wav"
    }
    """
    # Rate limit check (temporarily disabled)
    # rate_info = rate_limiter.check(session_id, len(request.text))
    rate_info = {"remaining": 999, "reset_iso": "N/A"}  # Placeholder

    # Validate voice
    if request.voice not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{request.voice}' not found. Available: {list(VOICES.keys())}"
        )
    
    # Validate text length
    if not (MIN_TEXT_LENGTH <= len(request.text) <= MAX_TEXT_LENGTH):
        raise HTTPException(
            status_code=400,
            detail=f"Text length must be between {MIN_TEXT_LENGTH} and {MAX_TEXT_LENGTH}"
        )
    
    # Check queue capacity
    if metrics.in_queue >= MAX_QUEUE_SIZE:
        raise HTTPException(
            status_code=503,
            detail=f"Server busy. Queue full ({MAX_QUEUE_SIZE} requests). Please try again later."
        )
    
    # Prepare output
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / request.output_file
    
    try:
        start_time = time.time()
        
        # Run inference with preloaded model and queue management
        generated_audio, sample_rate, remove_silence_flag = await run_inference(
            text=request.text,
            voice_id=request.voice,
            speed=request.speed,
            remove_silence=False
        )
        
        # Save audio
        torchaudio.save(str(output_path), generated_audio, sample_rate)
        
        # Apply silence removal if requested (matches CLI behavior)
        if remove_silence_flag:
            remove_silence_for_generated_wav(str(output_path))
        
        generation_time = time.time() - start_time
        
        response = {
            "status": "success",
            "voice": request.voice,
            "text": request.text,
            "output_file": str(output_path),
            "duration": float(generated_audio.shape[-1] / sample_rate),
            "generation_time": round(generation_time, 2),
            "queue_position": metrics.in_queue,
            "message": "Speech synthesized successfully"
        }
        
        headers = {
            "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
            "X-RateLimit-Remaining": str(rate_info["remaining"]),
            "X-RateLimit-Reset": rate_info["reset_iso"],
            "X-Generation-Time": str(round(generation_time, 2)),
            "X-Queue-Position": str(metrics.in_queue)
        }
        
        return JSONResponse(content=response, headers=headers)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Synthesis failed: {str(e)}"
        )


@app.get("/tts/generate-audio")
async def tts_generate_audio(
    text: str = Query(...),
    voice_id: str = Query(...),
    speed: float = Query(1.0),
    remove_silence: bool = Query(False),
    cfg_strength: float = Query(2.0),
    nfe_step: int = Query(32)
):
    """
    Generate speech with Server-Sent Events (SSE) for real-time progress updates.
    Uses preloaded model for faster inference.
    """
    # Validate inputs
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
    
    # Apply Redis-backed rate limiting (temporarily disabled)
    # rate_info = rate_limiter.check(session_id, len(text))
    rate_info = {"remaining": 999, "reset_iso": "N/A"}  # Placeholder
    
    # Check queue capacity
    if metrics.in_queue >= MAX_QUEUE_SIZE:
        raise HTTPException(status_code=503, detail="Server is busy. Please try again later.")
    
    voice_config = VOICES[voice_id]
    ref_audio_path = REF_AUDIO_DIR / voice_config["audio"]
    
    if not ref_audio_path.exists():
        raise HTTPException(status_code=500, detail=f"Reference audio not found: {ref_audio_path}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = f"output_{int(time.time())}.wav"
    output_path = OUTPUT_DIR / output_file
    
    async def generate_progress() -> AsyncGenerator[str, None]:
        """Stream progress updates via SSE"""
        start_time = time.time()
        
        try:
            # Send initial progress
            yield f"data: {json.dumps({'progress': 0, 'status_key': 'initializing'})}\n\n"
            
            # Processing text
            yield f"data: {json.dumps({'progress': 10, 'status': 'Đang xử lý văn bản...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Loading reference audio (cached)
            yield f"data: {json.dumps({'progress': 20, 'status': 'Đang tải tham chiếu âm thanh...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Running inference (this is where the model processes)
            yield f"data: {json.dumps({'progress': 30, 'status': 'Đang tạo audio với mô hình...'})}\n\n"
            
            # Call preloaded model inference
            generated_audio, sample_rate, remove_silence_flag = await run_inference(
                text=text,
                voice_id=voice_id,
                speed=speed,
                remove_silence=remove_silence
            )
            
            # Inference complete
            yield f"data: {json.dumps({'progress': 80, 'status': 'Đã tạo xong audio...'})}\n\n"
            await asyncio.sleep(0.1)
            
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
                
                # Calculate file size and duration
                file_size = output_path.stat().st_size
                audio_duration = generated_audio.shape[-1] / sample_rate
                
                generation_time = time.time() - start_time
                
                # Send completion with file URL instead of base64 data (avoids chunk size limit)
                result_data = {
                    'progress': 100,
                    'status_key': 'complete',
                    'audio_data': audio_b64,
                    'filename': output_file,
                    'duration': audio_duration,
                    'file_size': file_size,
                    'generation_time': round(generation_time, 2)
                }
                yield f"data: {json.dumps(result_data)}\n\n"
            else:
                yield f"data: {json.dumps({'progress': 0, 'status_key': 'error', 'error_key': 'outputFileNotCreated'})}\n\n"
                
        except HTTPException as e:
            # Re-raise HTTP exceptions (like queue full)
            yield f"data: {json.dumps({'progress': 0, 'status': 'Lỗi', 'error': e.detail})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'progress': 0, 'status_key': 'error', 'error': str(e)})}\n\n"
    
    headers = {
        "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
        "X-RateLimit-Remaining": str(rate_info["remaining"]),
        "X-RateLimit-Reset": rate_info["reset_iso"],
        "X-Queue-Position": str(metrics.in_queue)
    }
    return StreamingResponse(generate_progress(), media_type="text/event-stream", headers=headers)


@app.get("/output/{filename}")
async def get_output_file(filename: str):
    """Serve generated audio files"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Security: prevent directory traversal
    if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/wav",
        filename=filename
    )


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
