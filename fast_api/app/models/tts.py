"""
TTS Request and Response models
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TTSRequest(BaseModel):
    """
    Request model for TTS synthesis
    """
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Text to synthesize",
        examples=["Xin chào các bạn"]
    )
    voice: str = Field(
        ...,
        description="Voice ID to use for synthesis",
        examples=["tran_ha_linh", "kha_banh", "chi_hang"]
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Speech speed (0.5 = slower, 2.0 = faster)"
    )
    remove_silence: bool = Field(
        default=False,
        description="Remove silence from generated audio"
    )
    
    # Advanced parameters (optional)
    nfe_step: Optional[int] = Field(
        default=None,
        ge=1,
        le=64,
        description="Number of function evaluations (quality vs speed)"
    )
    cfg_strength: Optional[float] = Field(
        default=None,
        ge=1.0,
        le=5.0,
        description="Classifier-free guidance strength"
    )
    sway_sampling_coef: Optional[float] = Field(
        default=None,
        description="Sway sampling coefficient"
    )
    
    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate and clean text"""
        v = v.strip()
        if not v:
            raise ValueError("Text cannot be empty")
        return v


class TTSResponse(BaseModel):
    """
    Response model for TTS synthesis
    """
    success: bool = Field(..., description="Whether synthesis succeeded")
    message: str = Field(..., description="Status message")
    audio_file: Optional[str] = Field(
        None,
        description="Path to generated audio file (if success)"
    )
    duration: Optional[float] = Field(
        None,
        description="Duration of generated audio in seconds"
    )
    sample_rate: Optional[int] = Field(
        None,
        description="Sample rate of generated audio"
    )
    from_cache: Optional[bool] = Field(
        None,
        description="Whether result was served from cache"
    )


class TTSProgress(BaseModel):
    """
    Progress update for SSE streaming
    """
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    status: str = Field(..., description="Current status message")
    file: Optional[str] = Field(None, description="Output file path when complete")
    error: Optional[str] = Field(None, description="Error message if failed")
