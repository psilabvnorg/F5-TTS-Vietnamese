"""
Health check and metrics models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueueMetrics(BaseModel):
    """
    Queue statistics
    """
    current_size: int = Field(..., description="Current queue size")
    max_size: int = Field(..., description="Maximum queue capacity")
    total_requests: int = Field(..., description="Total requests processed")
    completed: int = Field(..., description="Successfully completed requests")
    failed: int = Field(..., description="Failed requests")


class ModelInfo(BaseModel):
    """
    Model information
    """
    loaded: bool = Field(..., description="Whether model is loaded")
    model_name: str = Field(..., description="Model name")
    vocoder_name: str = Field(..., description="Vocoder name")
    vocab_file: Optional[str] = Field(None, description="Vocab file path")
    device: Optional[str] = Field(None, description="Device (cuda/cpu)")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate")


class CacheInfo(BaseModel):
    """
    Cache statistics (if Redis enabled)
    """
    connected: bool = Field(..., description="Redis connection status")
    total_keys: Optional[int] = Field(None, description="Total cached keys")
    ref_audio_cached: Optional[int] = Field(None, description="Cached reference audios")
    results_cached: Optional[int] = Field(None, description="Cached results")
    hit_rate_percent: Optional[float] = Field(None, description="Cache hit rate")


class HealthResponse(BaseModel):
    """
    Health check response
    """
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    model: ModelInfo = Field(..., description="Model information")
    queue: QueueMetrics = Field(..., description="Queue metrics")
    cache: Optional[CacheInfo] = Field(None, description="Cache info (if enabled)")
    capacity: Dict[str, int] = Field(
        ...,
        description="Capacity information"
    )
