"""
Tests for voice management endpoints
"""

import pytest
from fastapi import status


class TestVoiceEndpoints:
    """Test voice management endpoints"""
    
    def test_list_voices(self, client, mock_model_handler):
        """Test listing all available voices"""
        response = client.get("/api/v1/voices/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "total" in data
        assert "voices" in data
        assert isinstance(data["voices"], list)
    
    def test_get_voice_by_id(self, client, mock_model_handler):
        """Test getting specific voice by ID"""
        response = client.get("/api/v1/voices/tran_ha_linh")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == "tran_ha_linh"
        assert data["name"] == "Trần Hà Linh"
        assert data["gender"] == "female"
        assert data["language"] == "vi"
    
    def test_get_nonexistent_voice(self, client, mock_model_handler):
        """Test getting voice that doesn't exist"""
        response = client.get("/api/v1/voices/nonexistent_voice")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        
        assert "detail" in data
    
    def test_list_voice_ids(self, client):
        """Test getting list of voice IDs"""
        response = client.get("/api/v1/voices/ids/list")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "voice_ids" in data
        assert "total" in data
        assert isinstance(data["voice_ids"], list)
        assert len(data["voice_ids"]) == data["total"]
    
    def test_filter_voices_by_gender(self, client):
        """Test filtering voices by gender"""
        response = client.get("/api/v1/voices/?gender=female")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All returned voices should be female
        for voice in data["voices"]:
            if "gender" in voice:
                assert voice["gender"] == "female"
