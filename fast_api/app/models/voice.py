"""
Voice configuration models
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class Voice(BaseModel):
    """
    Voice metadata
    """
    id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Voice description")
    language: str = Field(..., description="Language code (e.g., 'vi')")
    gender: str = Field(..., description="Voice gender")
    audio_path: str = Field(..., description="Path to reference audio file")
    ref_text: str = Field(..., description="Reference text for voice")
    thumbnail: str = Field(..., description="URL to thumbnail image")
    sample_audio: str = Field(..., description="URL to sample audio")


class VoiceList(BaseModel):
    """
    List of available voices
    """
    total: int = Field(..., description="Total number of voices")
    voices: List[Voice] = Field(..., description="List of voice configurations")


class VoiceConfig(BaseModel):
    """
    Internal voice configuration (from config/voices.py)
    """
    name: str
    description: str
    language: str
    gender: str
    audio: str
    ref_text: str
    thumbnail: str
    sample_audio: str
