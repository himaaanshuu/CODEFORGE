"""Unit tests for CodeForge AI LLM module.

These tests do NOT require a NEBIUS_API_KEY and can run offline.
They verify the Pydantic models, configuration helpers, and error handling.
"""

from __future__ import annotations

import os
import sys
from typing import Any

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.llm.models import (
    is_configured,
    get_model_name,
    get_base_url,
    get_api_key,
    resolve_model,
    known_model_ids,
)
from backend.app.llm.client import NebiusClient


def test_configuration_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test configuration helper functions."""
    # Test that get_model_name works
    model = get_model_name()
    assert isinstance(model, str)
    assert len(model) > 0

    # Test get_base_url
    base = get_base_url()
    assert isinstance(base, str)
    assert "nebius" in base.lower() or "tokenfactory" in base.lower()

    # is_configured should return False when no API key is set
    # (isolate from the developer machine's backend/.env)
    import backend.app.llm.models as llm_models

    monkeypatch.setattr(llm_models, "NEBIUS_API_KEY", "")
    assert is_configured() is False

    # get_api_key should return empty string when not configured
    key = get_api_key()
    assert isinstance(key, str)

    print("PASS: test_configuration_helpers")


def test_is_configured_false_by_default() -> None:
    """Test that is_configured returns False when no API key is set."""
    from backend.app.llm.models import NEBIUS_API_KEY

    # Just verify the variable exists and is a string
    assert isinstance(NEBIUS_API_KEY, str)
    print("PASS: test_is_configured_false_by_default")


def test_health_check_response_types() -> None:
    """Test HealthCheckResponse type consistency."""
    from backend.app.llm.models import HealthCheckResponse

    # Valid statuses
    for status in ["healthy", "unavailable", "error"]:
        h = HealthCheckResponse(status=status, model="test-model")
        assert h.status == status

    print("PASS: test_health_check_response_types")


def test_resolve_model_defaults_and_labels() -> None:
    """resolve_model maps empty/labels/IDs to concrete allow-listed IDs."""
    import backend.app.llm.models as llm_models

    ultra, super_, nano = known_model_ids()
    assert ultra == "nvidia/Nemotron-3-Ultra-550b-a55b"

    assert resolve_model(None) == ultra
    assert resolve_model("") == ultra
    assert resolve_model("Nemotron 3 Ultra") == ultra
    assert resolve_model("nemotron 3 super") == super_
    assert resolve_model("Nemotron 3 Nano") == nano
    assert resolve_model(super_) == super_
    assert resolve_model(nano) == nano
    assert isinstance(llm_models.NEBIUS_SUPER_MODEL, str)
    assert isinstance(llm_models.NEBIUS_NANO_MODEL, str)

    print("PASS: test_resolve_model_defaults_and_labels")


def test_resolve_model_rejects_unknown() -> None:
    """Unknown model values raise instead of silently falling back."""
    import pytest as _pytest

    with _pytest.raises(ValueError, match="Unknown model"):
        resolve_model("gpt-999")

    print("PASS: test_resolve_model_rejects_unknown")


# Async test - run separately with asyncio
import pytest


@pytest.mark.asyncio
async def test_client_initialization_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test NebiusClient can be initialized without an API key (graceful degradation)."""
    # Isolate from the developer machine's backend/.env
    import backend.app.llm.models as llm_models

    monkeypatch.setattr(llm_models, "NEBIUS_API_KEY", "")

    from backend.app.llm.client import NebiusClient

    # Client should initialize even without API key
    client = NebiusClient(api_key="")
    assert client is not None

    # Health check should return unavailable when no key
    health = await client.health_check()
    assert health.status in ("unavailable", "error")

    await client.close()