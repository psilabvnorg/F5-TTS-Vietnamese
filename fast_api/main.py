#!/usr/bin/env python3
"""
Simple FastAPI server for F5-TTS Vietnamese inference
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
from glob import glob

app = FastAPI(title="F5-TTS Vietnamese API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set HuggingFace cache
os.environ["HF_HOME"] = "/home/psilab/.cache/huggingface"
os.environ["HF_HUB_CACHE"] = "/home/psilab/.cache/huggingface/hub"

# Base paths
BASE_DIR = Path(__file__).parent.parent
REF_AUDIO_DIR = BASE_DIR / "original_voice_ref"
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = BASE_DIR / "fast_api" / "static"
SAMPLES_DIR = STATIC_DIR / "samples"

# Available voices with metadata
VOICES = {
    "tran_ha_linh": {
        "name": "Trần Hà Linh",
        "description": "Female voice, clear pronunciation, suitable for narration",
        "language": "vi",
        "gender": "female",
        "audio": "tran_ha_linh/tran_ha_linh_trimmed.wav",
        "ref_text": "công khai điểm luôn, hồi đó là toán tám phẩy năm, văn sau phẩy năm, tiếng anh chín phẩy bao nhiêu ấy, còn lịch sử cũng chín phẩy bao nhiêu luôn, được chưa, vô đê lên coi, có bảng điểm trên thớt đó",
        "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
        "sample_audio": "/static/samples/tran_ha_linh_sample.wav"
    },
    "kha_banh": {
        "name": "Khá Bảnh",
        "description": "Male voice, energetic tone, conversational style",
        "language": "vi",
        "gender": "male",
        "audio": "kha_banh/kha_banh.wav",
        "ref_text": "đang khai trương ở quế võ thì à hôm đấy đi ăn, đi ăn thì uống rượu say ở quế võ rồi, thế xong là anh em ở quế võ lại rủ lên ba quê võ, thì là đến lúc nó đi lên ba",
        "thumbnail": "/static/thumbnails/kha_banh.jpg",
        "sample_audio": "/static/samples/kha_banh_sample.wav"
    },
    "chi_hang": {
        "name": "Chi Hang",
        "description": "Female voice, warm tone, friendly style",
        "language": "vi",
        "gender": "female",
        "audio": "chi_hang/chi_hang_trimmed.wav",
        "ref_text": "mày kể cho tao nghe trời ơi này ông cưng mày lắm nha, ông cưng lắm mà biết sao cuối cùng cũng chính mày kể cho tao nghe là ông bỏ mày ông đi theo coi như con hương tràm",
        "thumbnail": "/static/thumbnails/chi_hang.jpg",
        "sample_audio": "/static/samples/chi_hang_sample.wav"
    },
    "quang_linh_vlog": {
        "name": "Quang Linh Vlog",
        "description": "Male voice, enthusiastic tone, vlog style",
        "language": "vi",
        "gender": "male",
        "audio": "quang_linh_vlog/quang_linh_trimmed.wav",
        "ref_text": "ối dồi ôi, sao lại như thế này, sao lại lên được một nghìn, nghìn, ối dồi ôi, không biết là các bạn có, có bấm bấm vui, hay là theo cái nhịp điệu của mình mà mọi người cứ",
        "thumbnail": "/static/thumbnails/quang_linh.jpg",
        "sample_audio": "/static/samples/quang_linh_sample.wav"
    },
    "son_tung_mtp": {
        "name": "Sơn Tùng M-TP",
        "description": "Male voice, smooth tone, music style",
        "language": "vi",
        "gender": "male",
        "audio": "son_tung_mtp/mtp_trimmed.wav",
        "ref_text": "và nếu như mọi người để ý rằng từ trước đến nay thì cách dùng mạng xã hội của em ý, thì, nó không có gì thay đổi cả, nhiều khi gọi điện cho bố mẹ em",
        "thumbnail": "/static/thumbnails/son_tung.jpg",
        "sample_audio": "/static/samples/son_tung_sample.wav"
    }
    ,
    "chi_phien": {
        "name": "Chi Phiến",
        "description": "Female voice, expressive speech",
        "language": "vi",
        "gender": "female",
        "audio": "chi_phien/chi_phien_trimmed.wav",
        "ref_text": "cả năm nay chị đã rất điêu đứng rồi, cho nên hãy yêu thương chị đi, để kết thúc mọi chuyện, chị sẽ tặng em một câu nói, bằng bốn thứ tiếng",
        "thumbnail": "/static/thumbnails/chi_phien.jpg",
        "sample_audio": "/static/samples/chi_phien_chi_phien_trimmed.wav"
    },
    "huan_hoa_hong": {
        "name": "Huấn Hoa Hồng",
        "description": "Male voice, motivational street style",
        "language": "vi",
        "gender": "male",
        "audio": "huan_hoa_hong/huan_rose_trimmed.wav",
        "ref_text": "em có làm cái gì đi nữa, nếu có phải trả giá em cũng xin chấp nhận, bởi vì anh, anh biết đấy. ra xã hội làm ăn buơn trải, liều thì ăn nhiều",
        "thumbnail": "/static/thumbnails/huan_hoa_hong.jpg",
        "sample_audio": "/static/samples/huan_hoa_hong_huan_rose_trimmed.wav"
    },
    "phim_tai_lieu": {
        "name": "Phim Tài Liệu",
        "description": "Male narration, formal documentary tone",
        "language": "vi",
        "gender": "male",
        "audio": "phim_tai_lieu/le_chuc_trimmed.wav",
        "ref_text": "huống chi thành đại la, kinh đô cũ của cao vương ở và nơi trung tâm trời đất, được thế rồng cuộn hổ ngồi, chính giữa nam bắc đông tây",
        "thumbnail": "/static/thumbnails/phim_tai_lieu.jpg",
        "sample_audio": "/static/samples/phim_tai_lieu_le_chuc_trimmed.wav"
    },
    "thoi_su_nam_ha_noi": {
        "name": "Thời Sự Nam Hà Nội",
        "description": "Male news anchor, northern accent",
        "language": "vi",
        "gender": "male",
        "audio": "thoi_su_nam_ha_noi/thoi_su_nam1_trimmed.wav",
        "ref_text": "kính chào quý vị mời quý vị cùng theo dõi bản tin, bão ca mơ ghi khoảng đêm nay rạng sáng mai sẽ đi vào biển đông, trở thành cơn bão số mười ba trong năm nay, dự báo bão rất mạnh ở",
        "thumbnail": "/static/thumbnails/thoi_su_nam_ha_noi.jpg",
        "sample_audio": "/static/samples/thoi_su_nam_ha_noi_thoi_su_nam1_trimmed.wav"
    },
    "thoi_su_nam_sai_gon": {
        "name": "Thời Sự Nam Sài Gòn",
        "description": "Male news anchor, southern accent",
        "language": "vi",
        "gender": "male",
        "audio": "thoi_su_nam_sai_gon/thoi_su_nam_sg_trimmed.wav",
        "ref_text": "thương hiệu phụ kiện ô tô hàng đầu việt nam với gần năm trăm đại lý trên toàn quốc, đã cho ra mắt sản phẩm bóng đèn pha ô tô, mang đến giải pháp chiếu sáng cho hàng triệu xe hơi phổ thông, tại việt nam",
        "thumbnail": "/static/thumbnails/thoi_su_nam_sai_gon.jpg",
        "sample_audio": "/static/samples/thoi_su_nam_sai_gon_thoi_su_nam_sg_trimmed.wav"
    },
    "thoi_su_nu_ha_noi": {
        "name": "Thời Sự Nữ Hà Nội",
        "description": "Female news anchor, northern accent",
        "language": "vi",
        "gender": "female",
        "audio": "thoi_su_nu_ha_noi/thoi_su_nu_trimmed.wav",
        "ref_text": "mời quý khán giả theo dõi bản tin của đài truyền hình việt nam, tỉnh khánh hòa và tỉnh đắc lắc hưởng ứng chiến dịch quang trung thần tốc xây dựng, và sửa chữa nhà cho các hộ dân bị thiệt hại sau lũ, khánh hòa khởi công",
        "thumbnail": "/static/thumbnails/thoi_su_nu_ha_noi.jpg",
        "sample_audio": "/static/samples/thoi_su_nu_ha_noi_thoi_su_nu_trimmed.wav"
    },
    "thoi_su_nu_sai_gon": {
        "name": "Thời Sự Nữ Sài Gòn",
        "description": "Female news anchor, southern accent",
        "language": "vi",
        "gender": "female",
        "audio": "thoi_su_nu_sai_gon/thoi_su_nu2_trimmed.wav",
        "ref_text": "để chuẩn bị xây dựng các văn kiện trình đại hội mười ba của đảng, hôm nay đồng chí phạm minh chính, ủy viên bộ chính trị, bí thư trung ương đảng, trưởng ban tổ chức trung ương, đã khảo sát và làm việc",
        "thumbnail": "/static/thumbnails/thoi_su_nu_sai_gon.jpg",
        "sample_audio": "/static/samples/thoi_su_nu_sai_gon_thoi_su_nu2_trimmed.wav"
    },
    "tien_bip": {
        "name": "Tiến Bịp",
        "description": "Male voice, colloquial style",
        "language": "vi",
        "gender": "male",
        "audio": "tien_bip/tien_bip2_trimmed.wav",
        "ref_text": "anh ơi đến giờ phút này ý anh ạ để mà nói rằng ý em là em ô kê hết anh thích thế nào em cũng chiều luôn đấy anh ạ không ngán con vợ nào cả",
        "thumbnail": "/static/thumbnails/tien_bip.jpg",
        "sample_audio": "/static/samples/tien_bip_tien_bip2_trimmed.wav"
    },
    "truong_con": {
        "name": "Trưởng Con",
        "description": "Male voice, emotional storytelling",
        "language": "vi",
        "gender": "male",
        "audio": "truong_con/truong_con_trimmed.wav",
        "ref_text": "có một người em nó ở hòa bình, vào làm phụ hồ, ở trong sài gòn ở quận một, mà em nó không có tiền",
        "thumbnail": "/static/thumbnails/truong_con.jpg",
        "sample_audio": "/static/samples/truong_con_truong_con_trimmed.wav"
    },
    "36": {
        "name": "36",
        "description": "Female conversational tone",
        "language": "vi",
        "gender": "female",
        "audio": "36/36_trimmed.wav",
        "ref_text": "mua năm mươi cái nem chua thanh hóa về, bỏ ra ăn hai ngày mới hết, ô trời anh nói vừa vừa phải phải thôi anh chi mà anh đúng, là phóng đại lên gớm",
        "thumbnail": "/static/thumbnails/36.jpg",
        "sample_audio": "/static/samples/36_36_trimmed.wav"
    },
    "37": {
        "name": "37",
        "description": "Male news-style narration",
        "language": "vi",
        "gender": "male",
        "audio": "37/37_trimmed.wav",
        "ref_text": "trước những ảnh hưởng lạm phát trên thế giới, các doanh nghiệp dệt may da giày việt nam, lâm vào trình trạng vô cùng khó khăn do đơn hàng sụt giảm, nhiều công ty",
        "thumbnail": "/static/thumbnails/37.jpg",
        "sample_audio": "/static/samples/37_37_trimmed.wav"
    }
}


class TTSRequest(BaseModel):
    voice: str = "tran_ha_linh"
    text: str
    speed: float = 1.0
    output_file: str = "output.wav"


@app.get("/")
def read_root():
    return {
        "message": "F5-TTS Vietnamese API",
        "available_voices": list(VOICES.keys())
    }


@app.get("/healthz")
def health_check():
    """Health check endpoint for frontend status monitoring"""
    return {
        "status": "ok",
        "service": "F5-TTS Vietnamese API",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
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
def synthesize(request: TTSRequest):
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
        "--model", "F5TTS_Base",
        "--ref_audio", str(ref_audio),
        "--ref_text", voice_config["ref_text"],
        "--gen_text", request.text,
        "--speed", str(request.speed),
        "--vocoder_name", "vocos",
        "--vocab_file", str(BASE_DIR / "model/vocab.txt"),
        "--ckpt_file", str(BASE_DIR / "model/model_last.pt"),
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
        
        return {
            "status": "success",
            "voice": request.voice,
            "text": request.text,
            "output_file": str(output_path),
            "message": "Speech synthesized successfully"
        }
        
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
    nfe_step: int = Query(32)
):
    """
    Generate speech with Server-Sent Events (SSE) for real-time progress updates.
    """
    # Validate inputs (same as tts_generate)
    if not text or len(text) < 1:
        raise HTTPException(status_code=400, detail="Text is required")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="Text length must be between 1 and 5000 characters")
    if voice_id not in VOICES:
        raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
    if not (0.5 <= speed <= 2.0):
        raise HTTPException(status_code=400, detail="Speed must be between 0.5 and 2.0")
    if not (1.0 <= cfg_strength <= 5.0):
        raise HTTPException(status_code=400, detail="cfg_strength must be between 1.0 and 5.0")
    
    voice_config = VOICES[voice_id]
    ref_audio_path = REF_AUDIO_DIR / voice_config["audio"]
    
    if not ref_audio_path.exists():
        raise HTTPException(status_code=500, detail=f"Reference audio not found: {ref_audio_path}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = f"output_{int(time.time())}.wav"
    output_path = OUTPUT_DIR / output_file
    
    command = [
        "f5-tts_infer-cli",
        "--model", "F5TTS_Base",
        "--ref_audio", str(ref_audio_path),
        "--ref_text", voice_config["ref_text"],
        "--gen_text", text,
        "--speed", str(speed),
        "--vocoder_name", "vocos",
        "--vocab_file", str(BASE_DIR / "model/vocab.txt"),
        "--ckpt_file", str(BASE_DIR / "model/model_last.pt"),
        "--output_dir", str(OUTPUT_DIR),
        "--output_file", output_file
    ]
    
    if remove_silence:
        command.append("--remove_silence")
    
    async def generate_progress() -> AsyncGenerator[str, None]:
        """Stream progress updates via SSE"""
        try:
            # Send initial progress
            yield f"data: {json.dumps({'progress': 0, 'status': 'Đang khởi tạo...'})}\n\n"
            
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
                    yield f"data: {json.dumps({'progress': progress, 'status': 'Đang xử lý văn bản...'})}\n\n"
                
                # Look for batch progress "X/Y"
                batch_match = re.search(r'(\d+)/(\d+)\s+\[', line_text)
                if batch_match:
                    current = int(batch_match.group(1))
                    total = int(batch_match.group(2))
                    total_batches = total
                    batch_count = current
                    # Map batch progress to 30-90%
                    progress = 30 + int((current / total) * 60)
                    status_msg = f'Đang tạo audio {current}/{total}...'
                    yield f"data: {json.dumps({'progress': progress, 'status': status_msg})}\n\n"
                
                # Look for percentage in progress bar
                percent_match = re.search(r'(\d+)%', line_text)
                if percent_match and batch_count > 0:
                    batch_progress = int(percent_match.group(1))
                    # Calculate overall progress
                    base_progress = 30 + int(((batch_count - 1) / total_batches) * 60)
                    progress = base_progress + int((batch_progress / 100) * (60 / total_batches))
                    progress = min(progress, 90)
                    status_msg = f'Đang tạo kết quả  {batch_count}/{total_batches}...'
                    yield f"data: {json.dumps({'progress': progress, 'status': status_msg})}\n\n"
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode != 0:
                yield f"data: {json.dumps({'progress': 0, 'status': 'Lỗi', 'error': 'Tạo audio thất bại'})}\n\n"
                return
            
            # Check if output file exists
            if output_path.exists():
                yield f"data: {json.dumps({'progress': 95, 'status': 'Đang hoàn thiện kết quả...'})}\n\n"
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
                    'status': 'Hoàn thành!',
                    'audio_data': audio_b64,
                    'filename': output_file,
                    'duration': audio_duration,
                    'file_size': file_size
                }
                yield f"data: {json.dumps(result_data)}\n\n"
            else:
                yield f"data: {json.dumps({'progress': 0, 'status': 'Lỗi', 'error': 'File đầu ra không được tạo'})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'progress': 0, 'status': 'Lỗi', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate_progress(), media_type="text/event-stream")


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
