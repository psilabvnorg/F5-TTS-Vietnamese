"""
Tests for TTS synthesis endpoints
"""

import pytest
from fastapi import status
from io import BytesIO
import json
import os
from pathlib import Path


class TestTTSEndpoints:
    """Test TTS synthesis endpoints"""
    
    def test_generate_audio_sse(self, client):
        """Test SSE streaming endpoint"""
        params = {
            "text": "Xin chào",
            "voice_id": "tran_ha_linh"
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        # SSE endpoint should return 200 with streaming
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_generate_audio_with_invalid_voice(self, client):
        """Test SSE endpoint with invalid voice"""
        params = {
            "text": "Xin chào",
            "voice_id": "invalid_voice"
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        # Should still return 200 but with error in stream
        assert response.status_code == status.HTTP_200_OK
    
    def test_generate_audio_with_empty_text(self, client):
        """Test SSE endpoint with empty text"""
        params = {
            "text": "",
            "voice_id": "tran_ha_linh"
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        # SSE endpoint returns 200 but with error in stream
        assert response.status_code == status.HTTP_200_OK
        # Check response contains error message
        response_text = response.text
        assert "error" in response_text or "Text cannot be empty" in response_text
    
    def test_generate_audio_with_custom_params(self, client):
        """Test SSE endpoint with custom parameters"""
        params = {
            "text": "Test audio",
            "voice_id": "tran_ha_linh",
            "speed": 1.5,
            "nfe_step": 16,
            "cfg_strength": 3.0
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_generate_audio_long_text(self, client):
        """Test SSE endpoint with long text (should chunk)"""
        # Create a long text
        long_text = "Xin chào các bạn. " * 50
        params = {
            "text": long_text,
            "voice_id": "tran_ha_linh"
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_generate_audio_with_remove_silence(self, client):
        """Test SSE endpoint with remove_silence parameter"""
        params = {
            "text": "Xin chào",
            "voice_id": "tran_ha_linh",
            "remove_silence": True
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_queue_status(self, client):
        """Test getting queue status"""
        response = client.get("/api/v1/tts/queue")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "current_size" in data
        assert "max_size" in data
        assert "total_requests" in data
    
    def test_generate_audio_creates_wav_file(self, client):
        """Test that generate-audio endpoint actually creates a WAV file"""
        params = {
            "text": "Đây là bài kiểm tra tạo file audio",
            "voice_id": "tran_ha_linh"
        }
        
        response = client.get("/api/v1/tts/generate-audio", params=params)
        
        assert response.status_code == status.HTTP_200_OK
        assert "text/event-stream" in response.headers.get("content-type", "")
        
        # Parse SSE response to find the final event with audio info
        response_text = response.text
        lines = response_text.split('\n')
        
        audio_url = None
        file_size = None
        duration = None
        
        for line in lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    if 'audio_url' in data:
                        audio_url = data['audio_url']
                        file_size = data.get('file_size')
                        duration = data.get('duration')
                        break
                except json.JSONDecodeError:
                    continue
        
        # Verify audio file metadata was returned
        assert audio_url is not None, "No audio_url found in SSE response"
        assert file_size is not None and file_size > 0, "Invalid file size"
        assert duration is not None and duration > 0, "Invalid duration"
        
        # Verify the file actually exists
        # audio_url format: /output/tts_tran_ha_linh_TIMESTAMP.wav
        filename = audio_url.split('/')[-1]
        # OUTPUT_DIR is BASE_DIR/output, which is parent.parent.parent.parent/output
        output_path = Path(__file__).parent.parent.parent.parent / "output" / filename
        
        assert output_path.exists(), f"Audio file not created at {output_path}"
        assert output_path.stat().st_size > 0, "Audio file is empty"
        
        # Cleanup test file
        output_path.unlink(missing_ok=True)

