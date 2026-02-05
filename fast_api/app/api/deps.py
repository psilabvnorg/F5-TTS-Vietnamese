"""
Shared dependencies for API endpoints
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status

from app.services.model_handler import F5TTSModelHandler
from app.core.events import get_model_handler


# Dependency injection for model handler
async def get_handler() -> F5TTSModelHandler:
    """
    Dependency to get the initialized model handler
    
    Raises:
        HTTPException: If model handler not available
    
    Returns:
        F5TTSModelHandler: The model handler instance
    """
    try:
        return get_model_handler()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please try again later."
        ) from e


# Type alias for dependency injection
ModelHandlerDep = Annotated[F5TTSModelHandler, Depends(get_handler)]
