"""
Pytest configuration and fixtures for F5-TTS API tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
import sys
from pathlib import Path
import shutil
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.api.deps import get_handler
from app.services.model_handler import F5TTSModelHandler


@pytest.fixture
def mock_model_handler():
    """Mock F5TTS model handler for testing without loading actual models"""
    handler = Mock(spec=F5TTSModelHandler)
    
    # Mock model info
    handler.get_model_info.return_value = {
        "model_name": "F5TTS_Base",
        "vocoder_name": "vocos",
        "vocab_file": "/path/to/vocab.txt",
        "checkpoint_file": "/path/to/model.pt"
    }
    
    # Mock inference method - create temporary copy of sample audio file
    def mock_infer(*args, **kwargs):
        # Get the sample audio file path
        sample_audio = Path(__file__).parent.parent / "static" / "samples" / "tran_ha_linh_tran_ha_linh_trimmed.wav"
        
        # Create a temporary copy that can be safely deleted
        temp_file = tempfile.mktemp(suffix=".wav")
        shutil.copy(sample_audio, temp_file)
        
        return (temp_file, 24000)
    
    handler.infer.side_effect = mock_infer
    
    # Mock voices
    handler.voices = {
        "tran_ha_linh": {
            "name": "Trần Hà Linh",
            "gender": "female",
            "language": "vi"
        }
    }
    
    return handler


@pytest.fixture
def client(mock_model_handler, monkeypatch):
    """Test client with mocked model handler"""
    
    # Override the dependency to return our mock
    async def override_get_handler():
        return mock_model_handler
    
    app.dependency_overrides[get_handler] = override_get_handler
    
    # Mock the startup handler initialization to prevent real model loading
    from app.core import events
    monkeypatch.setattr(events, "_model_handler", mock_model_handler)
    
    # Also mock the get_model_handler function to return our mock
    def mock_get_model_handler():
        return mock_model_handler
    
    monkeypatch.setattr(events, "get_model_handler", mock_get_model_handler)
    
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_tts_request():
    """Sample TTS request payload"""
    return {
        "text": "Xin chào các bạn",
        "voice": "tran_ha_linh",
        "speed": 1.0
    }


@pytest.fixture
def sample_voices():
    """Sample voice configurations"""
    return {
        "tran_ha_linh": {
            "name": "Trần Hà Linh",
            "description": "Female voice, clear pronunciation",
            "language": "vi",
            "gender": "female",
            "audio": "tran_ha_linh/tran_ha_linh_trimmed.wav",
            "ref_text": "công khai điểm luôn",
            "thumbnail": "/static/thumbnails/tran_ha_linh.jpg",
            "sample_audio": "/static/samples/tran_ha_linh_sample.wav"
        },
        "kha_banh": {
            "name": "Khá Bảnh",
            "description": "Male voice, energetic tone",
            "language": "vi",
            "gender": "male",
            "audio": "kha_banh/kha_banh.wav",
            "ref_text": "đang khai trương ở quế võ",
            "thumbnail": "/static/thumbnails/kha_banh.jpg",
            "sample_audio": "/static/samples/kha_banh_sample.wav"
        }
    }
