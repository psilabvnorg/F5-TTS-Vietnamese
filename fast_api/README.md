# F5-TTS Vietnamese API

FastAPI server for Vietnamese text-to-speech synthesis with preloaded F5-TTS model.

## Project Structure

```
fast_api/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── api/
│   │   ├── deps.py             # Dependency injection
│   │   └── v1/endpoints/       # API endpoints (tts, voices, health, samples)
│   ├── core/
│   │   ├── config.py          # Settings (Pydantic)
│   │   ├── events.py          # Startup/shutdown (model preloading)
│   │   ├── logging.py         # Logging setup
│   │   └── voices.py          # Voice configurations
│   ├── models/                 # Pydantic models (tts, voice, health)
│   └── services/
│       └── model_handler.py   # F5TTS inference handler
├── static/                     # Web UI (index.html, app.js, styles.css)
├── scripts/
│   ├── start.sh               # Startup script
│   └── test_api.sh            # API test script
├── tests/                      # Test suite
└── requirements.txt           # Dependencies
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
./scripts/start.sh

# Or with uvicorn directly
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Access:**
- Web UI: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

## API Endpoints

### TTS Synthesis

```bash
# Synthesize speech
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào", "voice": "tran_ha_linh", "speed": 1.0}' \
  --output output.wav

# Queue status
curl "http://localhost:8000/api/v1/tts/queue"

# SSE streaming
curl -N "http://localhost:8000/api/v1/tts/generate-audio?text=xin+chào&voice=tran_ha_linh"
```

### Voice Management

```bash
# List all voices
curl "http://localhost:8000/api/v1/voices/"

# Get specific voice
curl "http://localhost:8000/api/v1/voices/tran_ha_linh"

# Get voice IDs
curl "http://localhost:8000/api/v1/voices/ids/list"
```

### Health & Monitoring

```bash
# Health check
curl "http://localhost:8000/api/v1/health/"

# Liveness/Readiness probes
curl "http://localhost:8000/api/v1/health/liveness"
curl "http://localhost:8000/api/v1/health/readiness"

# Metrics
curl "http://localhost:8000/api/v1/health/metrics"
```

## Configuration

Edit `app/core/config.py` or use environment variables:

```python
# Key settings
MODEL_NAME = "F5TTS_Base"
VOCODER_NAME = "vocos"
LOAD_VOCODER_FROM_LOCAL = False
VOCODER_LOCAL_PATH = ""
MAX_QUEUE_SIZE = 50
MAX_CONCURRENT_INFERENCE = 1
PORT = 8000
HOST = "0.0.0.0"
```

**Environment variables:**
```bash
export PORT=8000
export LOG_LEVEL=DEBUG
export LOAD_VOCODER_FROM_LOCAL=true
python -m uvicorn app.main:app
```

## Features

- **Model Preloading**: Loaded at startup for fast inference
- **Queue Management**: Async semaphore for GPU serialization
- **API Versioning**: `/api/v1/` endpoints
- **Web UI**: Browser-based interface
- **Health Checks**: Kubernetes-ready liveness/readiness probes

## Development

```bash
# Run tests
./scripts/run_tests.sh

# Or with pytest directly
pytest tests/ -v

# Run specific test file
pytest tests/test_api/test_health.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

**Add new endpoint:**
1. Create file in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/__init__.py`
3. Update models in `app/models/`
4. Add tests in `tests/test_api/`

## Troubleshooting

**Import errors:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Port in use:**
```bash
python -m uvicorn app.main:app --port 8001
```

**Model paths:** Check `app/core/config.py` for `MODEL_DIR`, `CHECKPOINT_FILE`, `VOCAB_FILE`
