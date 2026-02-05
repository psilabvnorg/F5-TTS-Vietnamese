"""
Application settings and configuration
Consolidates existing config/ folder into modern Pydantic settings
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # ==========================================
    # API Metadata
    # ==========================================
    APP_NAME: str = "F5-TTS Vietnamese API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Text-to-Speech API with preloaded F5-TTS model"
    
    # ==========================================
    # CORS Settings
    # ==========================================
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # ==========================================
    # Path Configuration
    # ==========================================
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    REF_AUDIO_DIR: Path = BASE_DIR / "original_voice_ref"
    OUTPUT_DIR: Path = BASE_DIR / "output"
    MODEL_DIR: Path = BASE_DIR / "model"
    
    @property
    def VOCAB_FILE(self) -> Path:
        return self.MODEL_DIR / "vocab.txt"
    
    @property
    def CHECKPOINT_FILE(self) -> Path:
        return self.MODEL_DIR / "model_last.pt"
    
    @property
    def STATIC_DIR(self) -> Path:
        return self.BASE_DIR / "fast_api" / "static"
    
    # ==========================================
    # Model Settings
    # ==========================================
    MODEL_NAME: str = "F5TTS_Base"
    VOCODER_NAME: str = "vocos"
    LOAD_VOCODER_FROM_LOCAL: bool = False
    VOCODER_LOCAL_PATH: str = ""
    
    # ==========================================
    # HuggingFace Cache Settings
    # ==========================================
    HF_HOME: str = os.getenv("HF_HOME", "/home/psilab/.cache/huggingface")
    HF_HUB_CACHE: str = os.getenv("HF_HUB_CACHE", "/home/psilab/.cache/huggingface/hub")
    
    # ==========================================
    # TTS Generation Settings
    # ==========================================
    SAMPLE_RATE: int = 24000
    MIN_TEXT_LENGTH: int = 1
    MAX_TEXT_LENGTH: int = 5000
    MIN_SPEED: float = 0.5
    MAX_SPEED: float = 2.0
    MIN_CFG_STRENGTH: float = 1.0
    MAX_CFG_STRENGTH: float = 5.0
    
    # Default inference parameters
    DEFAULT_NFE_STEP: int = 32
    DEFAULT_CFG_STRENGTH: float = 2.0
    DEFAULT_SWAY_SAMPLING_COEF: float = -1.0
    DEFAULT_TARGET_RMS: float = 0.1
    DEFAULT_CROSS_FADE_DURATION: float = 0.15
    
    # ==========================================
    # Queue & Concurrency
    # ==========================================
    MAX_QUEUE_SIZE: int = 50
    MAX_CONCURRENT_INFERENCE: int = 1
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW: int = 3600  # seconds (1 hour)
    
    # ==========================================
    # Redis Cache Settings (optional)
    # ==========================================
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TTL_RESULTS: int = 3600      # 1 hour
    REDIS_TTL_REF_AUDIO: int = 86400   # 24 hours
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==========================================
    # Server Settings
    # ==========================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    WORKERS: int = 1
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()


# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist"""
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if settings.STATIC_DIR.exists():
        (settings.STATIC_DIR / "samples").mkdir(parents=True, exist_ok=True)


# Call on import
ensure_directories()
