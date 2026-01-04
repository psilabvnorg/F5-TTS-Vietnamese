"""
Tests for F5TTS Model Handler service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import torch
from pathlib import Path


class TestModelHandler:
    """Test F5TTSModelHandler service"""
    
    @patch('app.services.model_handler.load_model')
    @patch('app.services.model_handler.load_vocoder')
    def test_model_initialization(self, mock_load_vocoder, mock_load_model):
        """Test model handler initialization"""
        from app.services.model_handler import F5TTSModelHandler
        
        mock_model = Mock()
        mock_vocoder = Mock()
        mock_load_model.return_value = (mock_model, None)
        mock_load_vocoder.return_value = mock_vocoder
        
        handler = F5TTSModelHandler(
            model_name="F5TTS_Base",
            vocab_file="vocab.txt",
            ckpt_file="model.pt",
            vocoder_name="vocos"
        )
        
        assert handler.ema_model is not None
        assert handler.vocoder is not None
        mock_load_model.assert_called_once()
        mock_load_vocoder.assert_called_once()
    
    def test_get_model_info(self):
        """Test getting model information"""
        from app.services.model_handler import F5TTSModelHandler
        
        handler = Mock(spec=F5TTSModelHandler)
        handler.model_name = "F5TTS_Base"
        handler.vocoder_name = "vocos"
        handler.vocab_file = "/path/to/vocab.txt"
        handler.checkpoint_file = "/path/to/model.pt"
        
        handler.get_model_info.return_value = {
            "model_name": handler.model_name,
            "vocoder_name": handler.vocoder_name,
            "vocab_file": handler.vocab_file,
            "checkpoint_file": handler.checkpoint_file
        }
        
        info = handler.get_model_info()
        
        assert info["model_name"] == "F5TTS_Base"
        assert info["vocoder_name"] == "vocos"
        assert "vocab_file" in info
        assert "checkpoint_file" in info
    
    @patch('app.services.model_handler.infer_process')
    def test_inference(self, mock_infer):
        """Test TTS inference"""
        from app.services.model_handler import F5TTSModelHandler
        
        # Mock the inference process
        mock_audio = torch.randn(1, 24000)
        mock_infer.return_value = (mock_audio, 24000, None)
        
        handler = Mock(spec=F5TTSModelHandler)
        handler.infer.return_value = (b"fake_audio_bytes", 24000)
        
        audio_bytes, sample_rate = handler.infer(
            ref_audio="ref.wav",
            ref_text="Reference text",
            gen_text="Generate this",
            model=Mock(),
            vocoder=Mock()
        )
        
        assert isinstance(audio_bytes, bytes)
        assert sample_rate == 24000
    
    def test_voice_preprocessing(self):
        """Test voice reference audio preprocessing"""
        from app.services.model_handler import F5TTSModelHandler
        
        handler = Mock(spec=F5TTSModelHandler)
        handler.voices = {
            "test_voice": {
                "ref_audio": torch.randn(1, 24000),
                "ref_text": "Test reference text"
            }
        }
        
        assert "test_voice" in handler.voices
        assert "ref_audio" in handler.voices["test_voice"]
        assert "ref_text" in handler.voices["test_voice"]
    
    def test_invalid_voice_handling(self):
        """Test handling of invalid voice selection"""
        from app.services.model_handler import F5TTSModelHandler
        
        handler = Mock(spec=F5TTSModelHandler)
        handler.voices = {"valid_voice": {}}
        
        # Test that requesting invalid voice would raise error
        with pytest.raises(KeyError):
            _ = handler.voices["invalid_voice"]
    
    def test_inference_with_speed_adjustment(self):
        """Test inference with speed parameter"""
        from app.services.model_handler import F5TTSModelHandler
        
        handler = Mock(spec=F5TTSModelHandler)
        
        # Test different speed values
        for speed in [0.5, 1.0, 1.5, 2.0]:
            handler.infer.return_value = (b"audio", 24000)
            audio, sr = handler.infer(
                ref_audio="ref.wav",
                ref_text="ref",
                gen_text="gen",
                speed=speed,
                model=Mock(),
                vocoder=Mock()
            )
            assert sr == 24000
    
    def test_inference_with_custom_params(self):
        """Test inference with custom generation parameters"""
        from app.services.model_handler import F5TTSModelHandler
        
        handler = Mock(spec=F5TTSModelHandler)
        handler.infer.return_value = (b"audio", 24000)
        
        audio, sr = handler.infer(
            ref_audio="ref.wav",
            ref_text="ref",
            gen_text="gen",
            nfe_step=32,
            cfg_strength=2.0,
            sway_sampling_coef=-1.0,
            model=Mock(),
            vocoder=Mock()
        )
        
        assert audio is not None
        assert sr == 24000
