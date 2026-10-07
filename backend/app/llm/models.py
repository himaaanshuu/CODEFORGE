from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


# Model configuration from environment
NEBIUS_BASE_URL: str = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_API_KEY: str
NEBIUS_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b"

# Try to load from environment at module level, but keep it configurable
try:
    import os
    NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
    NEBIUS_MODEL = os.getenv("NEBIUS_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
except ImportError:
    NEBIUS_API_KEY = ""
    NEBIUS_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"


# --- Pydantic request/response models ---


class LLMGenerateRequest(BaseModel):
    """Request model for LLM generation."""

    prompt: str = Field(
        ...,
        description="The prompt to send to the model.",
    ),
    model: Optional[str] = Field(
        None,
        description="Override the default model (NEBIUS_MODEL env var).",
    ),
    temperature: Optional[float] = Field(
        0.7,
        description="Sampling temperature (0-2).",
        ge=0.0,
        lte=2.0,
    ),
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum tokens to generate.",
        gt=0,
    ),
    stream: Optional[bool] = Field(
        False,
        description="Whether to stream the response.",
    ),
    stop: Optional[str] = Field(
        None,
        description="Stop generation on this token.",
    ),
    top_p: Optional[float] = Field(
        1.0,
        description="Top-p nucleus sampling.",
        gt=0.0,
        lte=1.0,
    )


class LLMGenerateResponse(BaseModel):
    """Response model for LLM generation."""

    success: bool = Field(..., description="Whether the generation succeeded.")
    model: str = Field(..., description="The model that was used.")
    response: str = Field(..., description="The model's generated response.")
    usage: Optional[dict] = Field(
        None,
        description="Token usage information (prompt, completion, total).",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if generation failed.",
    )


class HealthCheckResponse(BaseModel):
    """Response model for LLM health check."""

    status: Literal["healthy", "unavailable", "error"] = Field(
        ...,
        description="Current LLM service status.",
    ),
    model: Optional[str] = Field(None, description="Configured model name."),
    message: Optional[str] = Field(None, description="Additional detail message.")


# --- Model configuration helpers ---


def get_model_name() -> str:
    """Return the currently configured model name."""
    return NEBIUS_MODEL


def get_base_url() -> str:
    """Return the Nebius API base URL."""
    return NEBIUS_BASE_URL


def is_configured() -> bool:
    """Check if the API key is set."""
    return bool(NEBIUS_API_KEY and NEBIUS_API_KEY.strip())


def get_api_key() -> str:
    """Return the API key (never log or expose this directly)."""
    return NEBIUS_API_KEY
