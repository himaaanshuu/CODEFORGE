from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field


# Model configuration from environment
NEBIUS_BASE_URL: str = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_API_KEY: str
NEBIUS_MODEL: str = "nvidia/Nemotron-3-Ultra-550b-a55b"
NEBIUS_SUPER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"
NEBIUS_NANO_MODEL: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

# Try to load from environment at module level, but keep it configurable
try:
    import os
    NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
    NEBIUS_MODEL = os.getenv("NEBIUS_MODEL", "nvidia/Nemotron-3-Ultra-550b-a55b")
    NEBIUS_SUPER_MODEL = os.getenv("NEBIUS_SUPER_MODEL", "nvidia/nemotron-3-super-120b-a12b")
    NEBIUS_NANO_MODEL = os.getenv("NEBIUS_NANO_MODEL", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")
except ImportError:
    NEBIUS_API_KEY = ""
    NEBIUS_MODEL = "nvidia/Nemotron-3-Ultra-550b-a55b"
    NEBIUS_SUPER_MODEL = "nvidia/nemotron-3-super-120b-a12b"
    NEBIUS_NANO_MODEL = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

# Display labels shown in the frontend model picker, resolved dynamically so
# tests / env overrides of the NEBIUS_*_MODEL vars always take effect.
def _label_map() -> dict[str, str]:
    return {
        "Nemotron 3 Ultra": NEBIUS_MODEL,
        "Nemotron 3 Super": NEBIUS_SUPER_MODEL,
        "Nemotron 3 Nano": NEBIUS_NANO_MODEL,
    }


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
        le=2.0,
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
        le=1.0,
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


def known_model_ids() -> list[str]:
    """Return the allow-listed Nebius model IDs for agent runs."""
    return [NEBIUS_MODEL, NEBIUS_SUPER_MODEL, NEBIUS_NANO_MODEL]


def resolve_model(value: Optional[str]) -> str:
    """Resolve a client-supplied model selection to a concrete model ID.

    Accepts ``None``/empty (→ default Ultra model), an exact allow-listed
    model ID, or a frontend display label such as ``"Nemotron 3 Super"``
    (matched case-insensitively). Anything else raises ``ValueError`` —
    callers turn that into a client-facing error instead of silently
    falling back, so a typo can never burn Ultra credits by accident.
    """
    if value is None or not str(value).strip():
        return NEBIUS_MODEL
    cleaned = str(value).strip()
    for known in known_model_ids():
        if cleaned == known:
            return known
    lowered = cleaned.lower()
    for known in known_model_ids():
        if lowered == known.lower():
            return known
    for label, model_id in _label_map().items():
        if lowered == label.lower():
            return model_id
    valid = ", ".join(known_model_ids())
    raise ValueError(f"Unknown model: {cleaned}. Valid models: {valid}")


def get_base_url() -> str:
    """Return the Nebius API base URL."""
    return NEBIUS_BASE_URL


def is_configured() -> bool:
    """Check if the API key is set."""
    return bool(NEBIUS_API_KEY and NEBIUS_API_KEY.strip())


def get_api_key() -> str:
    """Return the API key (never log or expose this directly)."""
    return NEBIUS_API_KEY
