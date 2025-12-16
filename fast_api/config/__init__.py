"""
Configuration module for F5-TTS Vietnamese API

Exports all configuration variables for easy importing:
    from config import VOICES, BASE_DIR, API_TITLE, etc.
"""

from .voices import VOICES
from .paths import (
    BASE_DIR,
    REF_AUDIO_DIR,
    OUTPUT_DIR,
    STATIC_DIR,
    SAMPLES_DIR,
    MODEL_DIR,
    VOCAB_FILE,
    CHECKPOINT_FILE
)
from .settings import (
    API_TITLE,
    API_VERSION,
    CORS_ALLOW_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    HF_HOME,
    HF_HUB_CACHE,
    MODEL_NAME,
    VOCODER_NAME,
    SAMPLE_RATE,
    MIN_TEXT_LENGTH,
    MAX_TEXT_LENGTH,
    MIN_SPEED,
    MAX_SPEED,
    MIN_CFG_STRENGTH,
    MAX_CFG_STRENGTH,
    RATE_LIMIT_REQUESTS
)

__all__ = [
    # Voices
    "VOICES",
    # Paths
    "BASE_DIR",
    "REF_AUDIO_DIR",
    "OUTPUT_DIR",
    "STATIC_DIR",
    "SAMPLES_DIR",
    "MODEL_DIR",
    "VOCAB_FILE",
    "CHECKPOINT_FILE",
    # Settings
    "API_TITLE",
    "API_VERSION",
    "CORS_ALLOW_ORIGINS",
    "CORS_ALLOW_CREDENTIALS",
    "CORS_ALLOW_METHODS",
    "CORS_ALLOW_HEADERS",
    "HF_HOME",
    "HF_HUB_CACHE",
    "MODEL_NAME",
    "VOCODER_NAME",
    "SAMPLE_RATE",
    "MIN_TEXT_LENGTH",
    "MAX_TEXT_LENGTH",
    "MIN_SPEED",
    "MAX_SPEED",
    "MIN_CFG_STRENGTH",
    "MAX_CFG_STRENGTH",
    "RATE_LIMIT_REQUESTS",
]
