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

## Testing
- Unit tests for each endpoint
- Integration tests for full workflows
- Load testing for concurrent requests
- Validation testing for input edge cases
- Error handling verification
- WebSocket connection stability tests
