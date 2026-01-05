# System Design: F5-TTS Vietnamese Workflow (Scalable)

## Overview
- Purpose: Convert input text to speech in a target character’s voice using a reference audio sample.
- Tech: Python (PyTorch), FastAPI, Uvicorn/ASGI, optional Gradio UI, GPU acceleration.
- Scope: This document covers service architecture, API design, scaling strategy, deployment, observability, security, and data flows for publishing the workflow.

## Architecture
- Client Frontend
  - Web UI for text + audio upload
  - Calls HTTP `POST /tts` on API service
- API Service (FastAPI)
  - Accepts multipart-form data (text + reference audio)
  - Validates & queues requests when needed
  - Manages model lifecycle (load once, reuse)
  - Streams/returns generated audio
- TTS Inference Core
  - `src/f5_tts/api.py` wraps model & vocoder loading and inference
  - Uses `f5_tts.infer.utils_infer` (preprocess, transcribe, infer_process)
- Job Queue (optional for scale)
  - Celery/RQ with Redis or RabbitMQ for asynchronous processing
  - Worker processes with GPU access run inference
- Storage
  - Input reference audio: ephemeral in memory or object storage (S3/MinIO)
  - Outputs: write WAV to object storage; return URL or stream
  - Model artifacts: local disk or Hugging Face cache
- Observability
  - Logging, metrics, tracing (Prometheus + Grafana; OpenTelemetry)
- Gateway & CDN (optional)
  - Nginx/Traefik in front of API
  - CDN for serving generated audio at scale

## Data Flow
1. User uploads text + reference audio
2. API validates, optionally stores upload & enqueues job
3. Worker loads model (on startup), performs inference
4. Result WAV stored (object storage) or streamed to client
5. API returns stream or signed URL

## API Design
- Endpoint: `POST /tts`
  - Request: `multipart/form-data`
    - `text`: string (required)
    - `voice`: file (required, WAV/MP3)
    - `ref_text`: string (optional) – transcript if known
    - `speed`: float (optional)
    - `remove_silence`: bool (optional)
  - Response:
    - `audio/wav` streaming response (sync path)
    - Or JSON `{ job_id, status, result_url }` (async path)
- Endpoint: `GET /jobs/{id}` (async)
  - Returns status & result URL when ready
- Health & Info:
  - `GET /healthz`, `GET /version`, `GET /config`

## Frontend
- Options:
  - Minimal HTML page posting `multipart/form-data` to `/tts`
  - React/Vue uploading via XHR/Fetch
  - Gradio (already present) for quick prototyping
- UX: file picker for voice, text input, speed toggle, progress indicator

## Model Lifecycle & Performance
- Load-once at process start using `F5TTS` in `src/f5_tts/api.py`
- Device selection: CUDA > XPU > MPS > CPU
- Warmup step on startup (optional) to reduce first-request latency
- Batch requests only if quality allows; otherwise one-request-per-model for deterministic outputs
- CPU path supported but slower; prefer GPU nodes with pinned model

## Scaling Strategy
- Vertical: Use GPU instances (A10/T4/A100) with sufficient VRAM; tune workers
- Horizontal: Multiple API pods behind a gateway; each pod loads model
- Async jobs: Offload long tasks to workers via Redis/RabbitMQ; return job ID
- Concurrency control:
  - Limit concurrent inferences per GPU to avoid OOM
  - Use a token/semaphore per worker
- Caching:
  - Cache reference preprocessing artifacts when repeat usage occurs
  - CDN cache for popular outputs
- Autoscaling:
  - HPA based on queue depth, latency, GPU utilization

## Deployment
- Containerize with existing `Dockerfile`
- Run `uvicorn` behind Nginx/Traefik
- Environments:
  - Dev: single machine, `.venv`, HF cache on disk
  - Staging/Prod: Kubernetes (GPU nodes), Helm chart or Compose
- Storage:
  - MinIO/S3 bucket for inputs/outputs
  - Persistent volume for HF model cache
- CI/CD:
  - Build & push Docker images
  - Smoke tests: `POST /healthz` and simple inference with short audio

## Reliability & Fault Tolerance
- Graceful shutdown with UVicorn lifespan events
- Request timeouts & max upload size limits
- Retry policy for transient storage errors
- Fallback to CPU if GPU unavailable (configurable)
- Circuit breakers at gateway when downstream is saturated

## Observability
- Structured logs (JSON): request IDs, latency, model version
- Metrics:
  - Request rate, success/error, p95 latency, GPU/VRAM utilization
- Tracing:
  - OpenTelemetry instrumentation for API and inference path
- Alerts:
  - OOM, high latency, queue backlog, low disk cache space

## Security
- AuthN:
  - API keys or OAuth2 for public endpoints
- AuthZ:
  - Rate limits per key/user
- Data:
  - Validate audio mime & duration limits
  - Virus/malware scanning for uploads (optional)
- Transport:
  - TLS via gateway
- Privacy:
  - Delete ephemeral input data after processing unless user opts to save

## Configuration & Feature Flags
- Env vars: `MODEL_NAME`, `CKPT_PATH`, `VOCODER_PATH`, `HF_CACHE_DIR`, `DEVICE`
- Tuning: `NFE_STEP`, `CFG_STRENGTH`, `TARGET_RMS`, `SPEED`
- Flags for sync vs async mode, output storage, silence removal

## Failure Modes & Mitigations
- HF cache miss or network failure → fallback to local checkpoints
- GPU OOM → reduce batch/concurrency, swap to CPU or lower model
- Corrupt input audio → reject with 400; detailed error message
- Long queue times → autoscale workers; preemption policy

## Roadmap
- Add gRPC for internal services
- Add job cancellation & progress updates via websockets
- Add speaker library management and reuse of preprocessed refs
- A/B test vocoder configurations and quality metrics (UTMOS)

## References in Repo
- API core: `src/f5_tts/api.py`
- Inference utils: `src/f5_tts/infer/utils_infer.py`
- FastAPI service examples: `fast_api/main.py`
- Scripts & examples: `src/f5_tts/infer/`, `script_infer/`, `script_utils/`
