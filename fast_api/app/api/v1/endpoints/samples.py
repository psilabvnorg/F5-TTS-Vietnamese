"""
Samples endpoint - list generated audio samples
"""

import os
from pathlib import Path
from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings


router = APIRouter()


class AudioSample(BaseModel):
    """Audio sample metadata"""
    voice: str
    filename: str
    url: str


class SamplesList(BaseModel):
    """List of audio samples"""
    samples: List[AudioSample]


@router.get("/", response_model=SamplesList)
async def list_samples():
    """
    List all audio samples from the samples directory
    """
    samples_dir = settings.STATIC_DIR / "samples"
    
    if not samples_dir.exists():
        return SamplesList(samples=[])
    
    samples = []
    for file in samples_dir.glob("*.wav"):
        # Extract voice name from filename (remove _trimmed.wav suffix)
        voice_name = file.stem.replace("_trimmed", "").replace("_", " ")
        
        samples.append(AudioSample(
            voice=voice_name,
            filename=file.name,
            url=f"/static/samples/{file.name}"
        ))
    
    # Sort by voice name
    samples.sort(key=lambda x: x.voice)
    
    return SamplesList(samples=samples)
