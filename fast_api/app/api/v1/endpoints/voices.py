"""
Voice management endpoints
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.models.voice import Voice, VoiceList
from app.core.config import settings
from app.core.logging import logger
from app.core.voices import VOICES


router = APIRouter()


def _load_voices() -> List[Voice]:
    """
    Load voice configurations from config
    """
    voices = []
    for voice_id, config in VOICES.items():
        voices.append(Voice(
            id=voice_id,
            name=config["name"],
            description=config["description"],
            language=config["language"],
            gender=config["gender"],
            audio_path=str(settings.REF_AUDIO_DIR / config["audio"]),
            ref_text=config["ref_text"],
            thumbnail=config["thumbnail"],
            sample_audio=config["sample_audio"]
        ))
    return voices


@router.get("/", response_model=VoiceList)
async def list_voices(gender: str = None):
    """
    Get list of available voices
    
    - **gender**: Optional filter by gender (male/female)
    
    Returns all available voice configurations with metadata
    """
    try:
        voices = _load_voices()
        
        # Filter by gender if specified
        if gender:
            voices = [v for v in voices if v.gender.lower() == gender.lower()]
        
        logger.info(f"Retrieved {len(voices)} voices")
        
        return VoiceList(
            total=len(voices),
            voices=voices
        )
    except Exception as e:
        logger.error(f"Failed to load voices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load voice configurations"
        ) from e


@router.get("/{voice_id}", response_model=Voice)
async def get_voice(voice_id: str):
    """
    Get details for a specific voice
    
    - **voice_id**: The unique identifier for the voice
    """
    if voice_id not in VOICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice '{voice_id}' not found"
        )
    
    config = VOICES[voice_id]
    
    return Voice(
        id=voice_id,
        name=config["name"],
        description=config["description"],
        language=config["language"],
        gender=config["gender"],
        audio_path=str(settings.REF_AUDIO_DIR / config["audio"]),
        ref_text=config["ref_text"],
        thumbnail=config["thumbnail"],
        sample_audio=config["sample_audio"]
    )


@router.get("/ids/list")
async def list_voice_ids():
    """
    Get simple list of voice IDs
    
    Returns just the voice IDs for quick reference
    """
    return {
        "voice_ids": list(VOICES.keys()),
        "total": len(VOICES)
    }
