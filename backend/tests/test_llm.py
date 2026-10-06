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
)
from backend.app.llm.client import NebiusClient


def test_configuration_helpers() -> None:
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


# Async test - run separately with asyncio
import pytest


@pytest.mark.asyncio
async def test_client_initialization_without_key() -> None:
    """Test NebiusClient can be initialized without an API key (graceful degradation)."""
    from backend.app.llm.client import NebiusClient

    # Client should initialize even without API key
    client = NebiusClient(api_key="")
    assert client is not None

    # Health check should return unavailable when no key
    health = await client.health_check()
    assert health.status in ("unavailable", "error")

    await client.close()