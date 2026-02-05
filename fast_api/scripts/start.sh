#!/bin/bash
# Start F5-TTS Vietnamese API with new structure

echo "=========================================="
echo "Starting F5-TTS Vietnamese API"
echo "=========================================="

# Activate virtual environment if exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
fi

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start server
echo "Starting FastAPI server..."
python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

echo "Server stopped."
