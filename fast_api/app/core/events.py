"""
Application startup and shutdown event handlers
"""

from typing import Optional
import asyncio

from app.core.config import settings
from app.services.model_handler import F5TTSModelHandler


# Global model handler instance
_model_handler: Optional[F5TTSModelHandler] = None


async def startup_event():
    """
    Load models and initialize resources on application startup
    """
    global _model_handler
    
    print("=" * 80)
    print(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    print("=" * 80)

    try:
        _model_handler = F5TTSModelHandler(
            model_name=settings.MODEL_NAME,
            ckpt_file=str(settings.CHECKPOINT_FILE),
            vocab_file=str(settings.VOCAB_FILE),
            model_cfg_path="",
            vocoder_name=settings.VOCODER_NAME,
            load_vocoder_from_local=settings.LOAD_VOCODER_FROM_LOCAL,
            vocoder_local_path=settings.VOCODER_LOCAL_PATH,
        )
        
        print("\nModel handler initialized successfully!")
        print(f"   Model: {settings.MODEL_NAME}")
        print(f"   Vocoder: {settings.VOCODER_NAME}")
        print(f"   Checkpoint: {settings.CHECKPOINT_FILE}")
        print(f"   Vocab: {settings.VOCAB_FILE}")
        
    except Exception as e:
        print(f"\nFailed to initialize model handler: {e}")
        raise
    
    print("\n" + "=" * 80)
    print("Application startup complete!")
    print(f"   API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"   Health Check: http://{settings.HOST}:{settings.PORT}/health")
    print("=" * 80 + "\n")


async def shutdown_event():
    """
    Cleanup resources on application shutdown
    """
    global _model_handler
    
    print("\n" + "=" * 80)
    print("Shutting down application...")
    print("=" * 80)
    
    # Clean up model handler if needed
    _model_handler = None
    
    print("Cleanup complete!")
    print("=" * 80 + "\n")


def get_model_handler() -> F5TTSModelHandler:
    """
    Dependency injection function to get the model handler instance
    
    Raises:
        RuntimeError: If model handler not initialized
    
    Returns:
        F5TTSModelHandler: The initialized model handler
    """
    if _model_handler is None:
        raise RuntimeError("Model handler not initialized. Call startup_event() first.")
    return _model_handler
