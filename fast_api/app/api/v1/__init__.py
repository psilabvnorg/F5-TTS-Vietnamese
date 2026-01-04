"""
API v1 router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import tts, voices, health, samples

# Create v1 router
api_router = APIRouter(prefix="/api/v1")

# Include endpoint routers
api_router.include_router(tts.router, prefix="/tts", tags=["TTS"])
api_router.include_router(voices.router, prefix="/voices", tags=["Voices"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(samples.router, prefix="/samples", tags=["Samples"])

__all__ = ["api_router"]
