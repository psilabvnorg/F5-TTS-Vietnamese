#!/bin/bash
# Run tests for F5-TTS API

echo "=========================================="
echo "Running F5-TTS API Tests"
echo "=========================================="

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run pytest with coverage
echo "Running tests..."
pytest tests/ -v --tb=short

echo ""
echo "=========================================="
echo "Test run complete"
echo "=========================================="
