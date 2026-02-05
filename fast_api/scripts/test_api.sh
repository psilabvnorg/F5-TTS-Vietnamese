#!/bin/bash
# Test the FastAPI server

echo "Testing F5-TTS API..."
echo ""

# Test 1: Get available voices
echo "1. Getting available voices:"
curl http://localhost:8000/voices
echo -e "\n"

# Test 2: Synthesize speech
echo "2. Synthesizing speech:"
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "voice": "tran_ha_linh",
    "text": "xin chào các bạn, đây là bài test giọng nói tiếng việt",
    "speed": 1.0,
    "output_file": "test_api_output.wav"
  }'
echo -e "\n"

echo "Done! Check output folder for test_api_output.wav"
