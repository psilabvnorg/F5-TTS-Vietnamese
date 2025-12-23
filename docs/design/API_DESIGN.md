# API Design: F5-TTS Vietnamese

## Overview
RESTful API for the F5-TTS Vietnamese voice cloning system. Provides endpoints for TTS generation, voice management, sample browsing, and system health monitoring.

**Base URL**: `http://localhost:8000`  
**API Version**: `v1`  
**Content Types**: `application/json`, `multipart/form-data`, `audio/wav`

---

## Authentication
Currently no authentication required for local deployment. Future versions may implement API key authentication.

---

## Core Endpoints

### 1. Health & Status

#### `GET /healthz`
Health check endpoint for monitoring service availability.

**Response** (200 OK):
```json
{
  "status": "ok",
  "service": "F5-TTS Vietnamese API",
  "timestamp": "2025-12-11T10:30:00Z",
  "version": "1.0.0"
}
```

**Use Case**: Frontend polls this endpoint to display Online/Busy status pill in header.

---

### 2. Voice Management

#### `GET /voices`
Retrieve all available preset voices with metadata.

**Response** (200 OK):
```json
{
  "voices": [
    {
      "id": "tran_ha_linh",
      "name": "Trần Hà Linh",
      "description": "Female voice, clear pronunciation, suitable for narration",
      "language": "vi",
      "gender": "female",
      "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
      "sample_audio": "/static/samples/tran_ha_linh_sample.wav",
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "kha_banh",
      "name": "Khá Bảnh",
      "description": "Male voice, energetic tone, conversational style",
      "language": "vi",
      "gender": "male",
      "thumbnail": "/static/thumbnails/kha_banh.jpg",
      "sample_audio": "/static/samples/kha_banh_sample.wav",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 2
}
```

**Error Response** (500):
```json
{
  "detail": "Failed to load voice configurations"
}
```

---

#### `GET voices/{voice_id}`
Get detailed information about a specific voice.

**Parameters**:
- `voice_id` (path): Voice identifier (e.g., "tran_ha_linh")

**Response** (200 OK):
```json
{
  "id": "tran_ha_linh",
  "name": "Trần Hà Linh",
  "description": "Female voice, clear pronunciation, suitable for narration",
  "language": "vi",
  "gender": "female",
  "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
  "sample_audio": "/static/samples/tran_ha_linh_sample.wav",
  "ref_text": "công khai điểm luôn, hồi đó là toán tám phẩy năm...",
  "duration": 5.2,
  "sample_rate": 24000,
  "created_at": "2025-01-01T00:00:00Z",
  "stats": {
    "total_generations": 1234,
    "avg_generation_time": 3.5
  }
}
```

**Error Response** (404):
```json
{
  "detail": "Voice 'invalid_id' not found"
}
```

---

### 3. TTS Generation

#### `POST tts/generate`
Generate speech from text using a preset voice.

**Request** (multipart/form-data):
```
text: "xin chào các bạn, hôm nay tôi sẽ giới thiệu về..."
voice_id: "tran_ha_linh"
speed: 1.0 (optional, default: 1.0, range: 0.5-2.0)
remove_silence: false (optional, default: false)
cfg_strength: 2.0 (optional, default: 2.0, range: 1.0-5.0)
nfe_step: 32 (optional, default: 32)
```

**Validation Rules**:
- `text`: Required, 1-5000 characters
- `voice_id`: Required, must exist in preset voices
- `speed`: Optional, float between 0.5 and 2.0
- `remove_silence`: Optional, boolean
- `cfg_strength`: Optional, float between 1.0 and 5.0
- `nfe_step`: Optional, integer, typically 16, 32, or 64

**Response** (200 OK):
- **Content-Type**: `audio/wav`
- **Headers**:
  ```
  Content-Disposition: attachment; filename="output.wav"
  X-Generation-Time: 3.2
  X-Audio-Duration: 15.5
  X-File-Size: 741600
  ```
- **Body**: Binary WAV audio data

**Error Responses**:

(400) Invalid input:
```json
{
  "detail": "Text length must be between 1 and 5000 characters"
}
```

(404) Voice not found:
```json
{
  "detail": "Voice 'invalid_voice' not found. Available: ['tran_ha_linh', 'kha_banh', ...]"
}
```

(500) Generation failed:
```json
{
  "detail": "TTS generation failed: [error details]",
  "error_code": "GENERATION_FAILED"
}
```

(503) Service busy:
```json
{
  "detail": "Service is currently processing another request. Please try again.",
  "retry_after": 5
}
```

---

#### `POST tts/generate-async`
Generate speech asynchronously (for longer texts or batch processing).

**Request** (application/json):
```json
{
  "text": "xin chào các bạn...",
  "voice_id": "tran_ha_linh",
  "speed": 1.0,
  "remove_silence": false,
  "cfg_strength": 2.0,
  "nfe_step": 32,
  "callback_url": "https://example.com/webhook" 
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "job_abc123xyz",
  "status": "queued",
  "created_at": "2025-12-11T10:30:00Z",
  "estimated_time": 10
}
```

---

#### `GET jobs/{job_id}`
Get status and result of an async TTS generation job.

**Parameters**:
- `job_id` (path): Job identifier

**Response** (200 OK) - Processing:
```json
{
  "job_id": "job_abc123xyz",
  "status": "processing",
  "progress": 45,
  "created_at": "2025-12-11T10:30:00Z",
  "started_at": "2025-12-11T10:30:05Z"
}
```

**Response** (200 OK) - Completed:
```json
{
  "job_id": "job_abc123xyz",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-12-11T10:30:00Z",
  "started_at": "2025-12-11T10:30:05Z",
  "completed_at": "2025-12-11T10:30:15Z",
  "generation_time": 10.2,
  "result": {
    "audio_url": "jobs/job_abc123xyz/download",
    "duration": 15.5,
    "file_size": 741600
  }
}
```

**Response** (200 OK) - Failed:
```json
{
  "job_id": "job_abc123xyz",
  "status": "failed",
  "created_at": "2025-12-11T10:30:00Z",
  "started_at": "2025-12-11T10:30:05Z",
  "failed_at": "2025-12-11T10:30:10Z",
  "error": {
    "message": "Model inference failed",
    "code": "MODEL_ERROR"
  }
}
```

**Status values**: `queued`, `processing`, `completed`, `failed`

---

#### `GET jobs/{job_id}/download`
Download the generated audio file for a completed job.

**Response** (200 OK):
- **Content-Type**: `audio/wav`
- **Body**: Binary WAV audio data

**Error Response** (404):
```json
{
  "detail": "Job 'job_invalid' not found or audio file unavailable"
}
```

---

#### `DELETE jobs/{job_id}`
Cancel a pending or processing job, or cleanup completed job resources.

**Response** (200 OK):
```json
{
  "message": "Job 'job_abc123xyz' cancelled successfully"
}
```

---

### 4. Sample Management

#### `GET samples`
Retrieve pre-generated sample audio files for preview.

**Query Parameters**:
- `voice_id` (optional): Filter samples by voice
- `limit` (optional): Number of samples to return (default: 20)
- `offset` (optional): Pagination offset (default: 0)

**Response** (200 OK):
```json
{
  "samples": [
    {
      "id": "sample_001",
      "title": "Giới thiệu sản phẩm",
      "description": "Mô tả về một sản phẩm công nghệ mới",
      "voice_id": "tran_ha_linh",
      "voice_name": "Trần Hà Linh",
      "audio_url": "/static/samples/sample_001.wav",
      "thumbnail": "/static/thumbnails/sample_001.jpg",
      "duration": 12.5,
      "text": "Xin chào quý khách...",
      "play_count": 456,
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "sample_002",
      "title": "Tin tức buổi sáng",
      "description": "Đọc bản tin thời sự",
      "voice_id": "thoi_su_nu_ha_noi",
      "voice_name": "Thời sự nữ Hà Nội",
      "audio_url": "/static/samples/sample_002.wav",
      "thumbnail": "/static/thumbnails/sample_002.jpg",
      "duration": 45.2,
      "text": "Tin nóng trong ngày...",
      "play_count": 789,
      "created_at": "2025-01-02T00:00:00Z"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

---

#### `POST samples/{sample_id}/play`
Track play count for analytics when user plays a sample.

**Response** (200 OK):
```json
{
  "sample_id": "sample_001",
  "play_count": 457
}
```

---

### 5. Custom Voice Upload (Future Enhancement)

#### `POST voices/upload`
Upload a custom reference audio file for voice cloning.

**Request** (multipart/form-data):
```
audio_file: [binary WAV file]
ref_text: "The transcription of the audio..."
voice_name: "My Custom Voice"
description: "Personal voice for testing"
```

**Validation**:
- `audio_file`: Required, WAV format, 5-30 seconds, mono or stereo
- `ref_text`: Required, must match audio content, 10-500 characters
- `voice_name`: Required, 1-100 characters
- `description`: Optional, max 500 characters

**Response** (201 Created):
```json
{
  "voice_id": "custom_voice_uuid123",
  "name": "My Custom Voice",
  "description": "Personal voice for testing",
  "audio_url": "voices/custom_voice_uuid123/audio",
  "ref_text": "The transcription of the audio...",
  "duration": 8.5,
  "created_at": "2025-12-11T10:30:00Z"
}
```

**Error Response** (400):
```json
{
  "detail": "Invalid audio format. Only WAV files are supported."
}
```

---

### 6. Metrics & Analytics

#### `GET metrics`
Get system metrics and statistics (admin endpoint).

**Response** (200 OK):
```json
{
  "system": {
    "uptime_seconds": 86400,
    "total_requests": 5432,
    "active_jobs": 2
  },
  "generation": {
    "total_generations": 5234,
    "successful": 5100,
    "failed": 134,
    "avg_generation_time": 3.5,
    "avg_audio_duration": 15.2
  },
  "voices": {
    "most_used": [
      {"voice_id": "tran_ha_linh", "count": 2341},
      {"voice_id": "kha_banh", "count": 1567}
    ]
  },
  "samples": {
    "total_plays": 12456,
    "most_played": [
      {"sample_id": "sample_002", "count": 789},
      {"sample_id": "sample_001", "count": 456}
    ]
  }
}
```

---

## Error Handling

### Standard Error Response Format
```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "timestamp": "2025-12-11T10:30:00Z",
  "path": "tts/generate"
}
```

### HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `202 Accepted`: Request accepted for async processing
- `400 Bad Request`: Invalid input or validation error
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `VOICE_NOT_FOUND`: Requested voice doesn't exist
- `GENERATION_FAILED`: TTS generation error
- `FILE_NOT_FOUND`: Audio file not available
- `SERVICE_BUSY`: System processing capacity reached
- `MODEL_ERROR`: ML model inference error
- `INVALID_FORMAT`: Unsupported file format

---

## Rate Limiting
- **Anonymous users**: 100 requests per hour per IP
- **With API key** (future): 1000 requests per hour
- Rate limit headers included in responses:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1702296600
  ```

---

## WebSocket (Future Enhancement)

### `WS ws/jobs`
Real-time job progress updates via WebSocket.

**Connection**: `ws://localhost:8000ws/jobs?job_id=job_abc123xyz`

**Messages from server**:
```json
{
  "type": "progress",
  "job_id": "job_abc123xyz",
  "progress": 45,
  "message": "Generating audio..."
}
```

```json
{
  "type": "completed",
  "job_id": "job_abc123xyz",
  "result": {
    "audio_url": "jobs/job_abc123xyz/download"
  }
}
```

---

## CORS Configuration
For frontend integration, CORS headers are enabled:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Request/Response Examples

### Example 1: Generate TTS with preset voice

**Request**:
```bash
curl -X POST "http://localhost:8000tts/generate" \
  -F "text=xin chào các bạn, hôm nay thời tiết rất đẹp" \
  -F "voice_id=tran_ha_linh" \
  -F "speed=1.0" \
  -o output.wav
```

**Response**: Binary WAV file downloaded as `output.wav`

---

### Example 2: List available voices

**Request**:
```bash
curl -X GET "http://localhost:8000voices"
```

**Response**:
```json
{
  "voices": [
    {
      "id": "tran_ha_linh",
      "name": "Trần Hà Linh",
      "description": "Female voice, clear pronunciation",
      "language": "vi",
      "gender": "female",
      "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
      "sample_audio": "/static/samples/tran_ha_linh_sample.wav"
    }
  ],
  "total": 1
}
```

---

### Example 3: Async generation with status check

**Step 1 - Submit job**:
```bash
curl -X POST "http://localhost:8000tts/generate-async" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "đây là một đoạn văn dài cần xử lý bất đồng bộ",
    "voice_id": "tran_ha_linh",
    "speed": 1.0
  }'
```

**Response**:
```json
{
  "job_id": "job_abc123xyz",
  "status": "queued"
}
```

**Step 2 - Check status**:
```bash
curl -X GET "http://localhost:8000jobs/job_abc123xyz"
```

**Response**:
```json
{
  "job_id": "job_abc123xyz",
  "status": "completed",
  "result": {
    "audio_url": "jobs/job_abc123xyz/download"
  }
}
```

**Step 3 - Download**:
```bash
curl -X GET "http://localhost:8000jobs/job_abc123xyz/download" \
  -o result.wav
```

---

## Implementation Notes

### Current Status
- ✅ Basic `/tts` endpoint implemented
- ✅ Voice configuration in `VOICES` dict
- ✅ Health check endpoint
- ⏳ Need to add `*` versioned endpoints
- ⏳ Need to add voice metadata (thumbnails, descriptions)
- ⏳ Need to implement samples endpoint
- ⏳ Need to add async job processing
- ⏳ Need to add metrics collection

### Next Steps
1. Refactor existing `/tts` to `tts/generate`
2. Add voice metadata to VOICES configuration
3. Create `voices` endpoint with full metadata
4. Implement `samples` endpoint
5. Add static file serving for thumbnails and samples
6. Implement async job queue (using Redis or in-memory queue)
7. Add WebSocket support for real-time updates
8. Implement basic rate limiting
9. Add metrics collection and `metrics` endpoint

### Dependencies
- FastAPI: Core API framework
- Pydantic: Request/response validation
- uvicorn: ASGI server
- aiofiles: Async file operations
- redis (optional): Job queue and caching
- python-multipart: Form data handling

---

## Security Considerations
- Input validation on all text inputs (XSS prevention)
- File upload validation (format, size, duration)
- Rate limiting to prevent abuse
- Sanitize file paths to prevent directory traversal
- API key authentication for production deployment
- HTTPS in production
- Log all requests for audit trail

---

## Performance Optimization
- Implement caching for frequently used voices
- Queue system for concurrent request handling
- Audio file compression options
- CDN for serving static samples and thumbnails
- Connection pooling for database/Redis
- Async processing for long-running tasks

---

## Concurrency & Scaling Strategy

### Hardware Context
**Target Deployment:**
- 1x RTX 3060 with 16GB VRAM
- Local workstation (PoC phase)
- Expected load: ~10 concurrent users

**F5-TTS Model Memory Requirements:**
- Model weights: ~2-3GB VRAM
- Vocoder: ~500MB VRAM
- Per-inference working memory: ~1-2GB VRAM
- **Total base load:** ~3.5GB VRAM

---

### Approach Comparison

#### **Option 1: AsyncIO + Queue (RECOMMENDED for PoC ✅)**

**Architecture:**
```
FastAPI → AsyncIO Queue → Single Model → Response
```

**How it works:**
- Single model loaded once in GPU memory
- Requests queued using asyncio.Queue
- Processed sequentially with async/await
- Simple semaphore/lock prevents concurrent GPU access

**Pros:**
- ✅ Simple to implement (50 lines of code)
- ✅ Minimal VRAM usage (~4GB total)
- ✅ No external dependencies
- ✅ Perfect for PoC validation
- ✅ Handles 10 users gracefully with queuing
- ✅ Easy to debug and maintain
- ✅ 1 hour implementation time

**Cons:**
- ❌ Sequential processing (one request at a time)
- ❌ Limited scalability beyond 20 concurrent users
- ❌ Not optimal for production at scale

**Expected Performance:**
- Per request: 2-5 seconds
- Throughput: 12-20 requests/minute
- With 10 concurrent users:
  - Average wait: ~15 seconds
  - Worst case (10th user): ~30 seconds
- This is acceptable for PoC with SSE progress updates

**Implementation Complexity:** Low (1 hour)

---

#### **Option 2: Ray Serve with Multiple Replicas**

**Architecture:**
```
Load Balancer → [Replica 1, Replica 2, Replica 3] → Responses
```

**How it works:**
- 2-3 model replicas on same GPU
- Each replica uses ~4GB VRAM
- Ray's load balancer distributes requests
- True parallel processing

**Pros:**
- ✅ True parallelism (2-3 concurrent inferences)
- ✅ Professional, production-grade architecture
- ✅ Built-in load balancing and monitoring
- ✅ Easy to scale horizontally
- ✅ Handles failures gracefully

**Cons:**
- ❌ VRAM intensive (8-12GB for 2-3 replicas)
- ❌ Requires Ray installation and setup
- ❌ Overkill for PoC phase
- ❌ More complex debugging
- ❌ 4-6 hours implementation time

**Expected Performance:**
- 2-3 requests processed simultaneously
- Throughput: 24-45 requests/minute
- With 10 concurrent users:
  - Average wait: ~5 seconds
  - Worst case: ~10 seconds

**VRAM Usage:** 8-12GB (may not fit on RTX 3060)

**Implementation Complexity:** Medium (4-6 hours)

---

#### **Option 3: Celery + Redis + Workers**

**Architecture:**
```
FastAPI → Redis Queue → [Worker 1, Worker 2] → Results → FastAPI
```

**How it works:**
- Redis manages distributed task queue
- Multiple Celery workers process tasks
- 2 workers sharing GPU sequentially
- Background job processing

**Pros:**
- ✅ Good for long-running, async tasks
- ✅ Task persistence and retry logic
- ✅ Can scale to multiple machines
- ✅ Familiar pattern for many developers
- ✅ Good monitoring tools

**Cons:**
- ❌ Requires Redis infrastructure
- ❌ More complex setup and deployment
- ❌ Overkill for local PoC
- ❌ Workers still process sequentially per GPU
- ❌ 6-8 hours implementation time

**Expected Performance:**
- 2 workers processing sequentially
- Throughput: 20-30 requests/minute
- With 10 concurrent users:
  - Average wait: ~10 seconds
  - Jobs queued in Redis

**VRAM Usage:** 8GB (2 workers × 4GB)

**Implementation Complexity:** High (6-8 hours)

---

#### **Option 4: Dynamic Batching**

**Architecture:**
```
FastAPI → Batch Collector (100-200ms) → Batch Inference → Split Results
```

**How it works:**
- Collect requests for 100-200ms window
- Process multiple texts in single forward pass
- F5-TTS processes batch together on GPU
- Split and return individual results

**Pros:**
- ✅ Most GPU-efficient approach
- ✅ 2-3x throughput improvement
- ✅ Best for high concurrent load
- ✅ Optimal VRAM utilization

**Cons:**
- ❌ Adds latency (100-200ms wait for batch)
- ❌ Requires F5-TTS batch inference support
- ❌ Very complex implementation
- ❌ May not work with current F5-TTS API
- ❌ 8-12 hours implementation time
- ❌ Difficult to debug

**Expected Performance:**
- 5-10 requests per batch
- Throughput: 30-50 requests/minute
- With 10 concurrent users:
  - Average wait: ~8 seconds (including batch wait)
  - Very consistent timing

**VRAM Usage:** 4-6GB

**Implementation Complexity:** Very High (8-12 hours)

---

### Detailed Comparison Table

| Metric | Option 1: Queue | Option 2: Ray | Option 3: Celery | Option 4: Batching |
|--------|-----------------|---------------|------------------|-------------------|
| **Implementation Time** | 1 hour | 4-6 hours | 6-8 hours | 8-12 hours |
| **VRAM Usage** | 4GB | 8-12GB | 8GB | 4-6GB |
| **Code Complexity** | Low | Medium | High | Very High |
| **External Dependencies** | None | Ray | Redis+Celery | Custom |
| **Concurrent Requests** | 1 | 2-3 | 2 | 5-10 (batched) |
| **Throughput (req/min)** | 12-20 | 24-40 | 20-30 | 30-50 |
| **Avg Wait (10 users)** | 15s | 5s | 10s | 8s |
| **PoC Ready** | ✅ Yes | ⚠️ Overkill | ❌ Too complex | ❌ Too complex |
| **Production Ready** | ⚠️ Limited | ✅ Yes | ✅ Yes | ✅ Yes |
| **Debug Difficulty** | Easy | Medium | Hard | Very Hard |
| **Scalability** | Low | High | High | Medium |
| **Maintenance** | Easy | Medium | Medium | Hard |
| **VRAM Fit (16GB GPU)** | ✅ Yes | ⚠️ Tight | ⚠️ Tight | ✅ Yes |

---

### Recommendation: Phased Approach

#### **Phase 1: Start with Option 1 (Week 1) ✅**

Implement simple AsyncIO queue for immediate PoC validation.

**Why:**
1. Get working PoC in 1 hour
2. Validate user experience with real users
3. Measure actual load patterns
4. Leaves VRAM headroom for monitoring
5. Easy to debug and iterate

**Performance Estimate:**
```
Scenario: 10 users request TTS simultaneously

User 1:  Wait 0s  → Process 3s → Total: 3s
User 2:  Wait 3s  → Process 3s → Total: 6s
User 3:  Wait 6s  → Process 3s → Total: 9s
User 4:  Wait 9s  → Process 3s → Total: 12s
User 5:  Wait 12s → Process 3s → Total: 15s
User 6:  Wait 15s → Process 3s → Total: 18s
User 7:  Wait 18s → Process 3s → Total: 21s
User 8:  Wait 21s → Process 3s → Total: 24s
User 9:  Wait 24s → Process 3s → Total: 27s
User 10: Wait 27s → Process 3s → Total: 30s

Average wait time: 15 seconds
Acceptable with SSE progress indicators!
```

**Key Features:**
- AsyncIO queue with semaphore
- Model preloaded once at startup
- Reference audio caching
- Real-time progress via SSE
- Queue position visibility

---

**Upgrade Paths:**

1. **If wait time > 15s + VRAM < 8GB:**
   - Upgrade to Ray Serve with 2 replicas
   - Implementation: 4 hours
   - Result: 2x throughput, 50% wait time

2. **If wait time > 10s + VRAM < 10GB:**
   - Add second model instance with simple lock
   - Implementation: 2 hours
   - Result: 1.8x throughput

3. **If wait time acceptable but want optimization:**
   - Optimize model loading/inference
   - Implement smarter caching
   - Fine-tune batch sizes
---

### Code Architecture Preview

#### Option 1 Implementation (Recommended Start)

```python
import asyncio
from collections import deque

# Global state
inference_semaphore = asyncio.Semaphore(1)  # 1 concurrent inference
request_queue = asyncio.Queue(maxsize=50)   # Max 50 queued
ref_audio_cache = {}                        # Cache preprocessed refs

# Preload model at startup (once)
F5TTS_model = load_model(...)
vocoder = load_vocoder(...)

async def run_inference(text: str, voice_id: str, speed: float):
    """Process one request with queue management"""
    
    # Wait for available slot
    async with inference_semaphore:
        # Get cached reference audio
        ref_audio, ref_text = ref_audio_cache[voice_id]
        
        # Run inference in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            _sync_inference,
            ref_audio, ref_text, text, speed
        )
        
        return result

def _sync_inference(ref_audio, ref_text, text, speed):
    """Actual inference (blocking)"""
    with torch.inference_mode():
        return infer_process(
            ref_audio=ref_audio,
            ref_text=ref_text,
            gen_text=text,
            model_obj=F5TTS_model,
            vocoder=vocoder,
            speed=speed
        )

@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    """API endpoint with automatic queuing"""
    
    # Check queue capacity
    if request_queue.qsize() >= 50:
        raise HTTPException(503, "Server busy")
    
    # Process with concurrency control
    result = await run_inference(
        request.text,
        request.voice,
        request.speed
    )
    
    return result
```

**Lines of Code:** ~80 lines  
**Dependencies:** None (built-in asyncio)  
**VRAM:** 4GB  
**Throughput:** 12-20 req/min

---

### Performance Benchmarks

#### Option 1: Queue (Target for PoC)
```
Load: 10 concurrent users
├── User 1:  3s (no wait)
├── User 2:  6s (wait 3s)
├── User 3:  9s (wait 6s)
├── User 4: 12s (wait 9s)
├── User 5: 15s (wait 12s)
├── User 6: 18s (wait 15s)
├── User 7: 21s (wait 18s)
├── User 8: 24s (wait 21s)
├── User 9: 27s (wait 24s)
└── User 10: 30s (wait 27s)

Avg wait: 15s
P95 wait: 27s
VRAM: 4GB
```

#### Option 2: Ray Serve (If needed)
```
Load: 10 concurrent users (2 replicas)
├── Batch 1 (2 users): 3s (no wait)
├── Batch 2 (2 users): 6s (wait 3s)
├── Batch 3 (2 users): 9s (wait 6s)
├── Batch 4 (2 users): 12s (wait 9s)
└── Batch 5 (2 users): 15s (wait 12s)

Avg wait: 6s
P95 wait: 12s
VRAM: 8GB (2 replicas × 4GB)
```

---

### Success Criteria

#### Phase 1 (PoC) Success Metrics:
- ✅ 10 concurrent users handled without crashes
- ✅ Average wait time < 20 seconds
- ✅ 95% success rate (< 5% errors)
- ✅ VRAM usage < 6GB (leaves headroom)
- ✅ User can see queue position and progress

#### Phase 2 (Production Ready) Goals:
- ✅ Average wait time < 10 seconds
- ✅ 99% success rate
- ✅ Handle 20+ concurrent users
- ✅ Graceful degradation under load
- ✅ Automatic scaling based on metrics

---

### Decision Framework

**When to stay with Option 1:**
- Average wait time < 15 seconds ✅
- Peak queue length < 20 users ✅
- User satisfaction acceptable ✅
- VRAM comfortable (< 8GB) ✅

**When to upgrade to Option 2 (Ray):**
- Average wait time > 15 seconds consistently ⚠️
- Peak queue length > 20 users ⚠️
- VRAM headroom available (< 10GB used) ✅
- Budget for 4-6 hours development time ✅

**When to consider Option 3 (Celery):**
- Need job persistence across restarts ⚠️
- Want to scale to multiple machines ⚠️
- Have Redis infrastructure already ✅
- Need complex workflow orchestration ⚠️

**When to implement Option 4 (Batching):**
- Consistently high concurrent load (20+ users) ⚠️
- F5-TTS supports batch inference ⚠️
- Need maximum throughput optimization ⚠️
- Have time for complex implementation (8-12 hours) ⚠️

---

## Testing
- Unit tests for each endpoint
- Integration tests for full workflows
- Load testing for concurrent requests
- Validation testing for input edge cases
- Error handling verification
- WebSocket connection stability tests
