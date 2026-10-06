#!/usr/bin/env python3
"""CLI smoke test for CodeForge AI Nebius/NVIDIA model integration.

Makes one real request to the configured NVIDIA model through Nebius Token Factory.
Exits gracefully if NEBIUS_API_KEY is not configured.

Do not print credentials or secret values.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

# Add the project root to the path so we can import backend package
# Script is at backend/scripts/test_nebius.py, so go up 3 levels
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.llm.client import get_client, shutdown, is_configured
from backend.app.llm.models import get_model_name, HealthCheckResponse


async def run_smoke_test() -> int:
    """Run the Nebius integration smoke test.

    Returns:
        0 if test passed (or gracefully skipped),
        1 if test failed due to configuration error.
    """
    print("Testing CodeForge AI LLM connection...")
    print(f"Provider: Nebius Token Factory")
    print(f"Model: {get_model_name()}")

    # Check if API key is configured
    if not is_configured():
        print("\n✗ NEBIUS_API_KEY not configured.")
        print("  Set NEBIUS_API_KEY in backend/.env to run the integration test.")
        print("  Get your free API key at: https://tokenfactory.nebius.com")
        return 1  # Configuration error, but not a crash

    print("\nPrompt: Explain recursion in simple terms.")

    try:
        client = get_client()

        response = await client.generate(
            prompt="Explain recursion in simple terms.",
            model=get_model_name(),
            temperature=0.7,
            max_tokens=200,
            top_p=1.0,
        )

        await client.close()

        if response.success:
            print("\nResponse:")
            print("---")
            # Print the response, but truncate if very long
            resp = response.response[:500] if response.response else "(empty)"
            print(resp)
            if len(response.response) > 500:
                print("  ... (truncated to 500 chars)")
            print("---")
            print("\n✓ Nebius/NVIDIA model connection successful.")
            return 0
        else:
            print("\n✗ Nebius model request failed:")
            print(f"  Error: {response.error}")
            # Don't expose any potential API key in the error
            await client.close()
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        await shutdown()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error during Nebius request: {str(e)[:200]}")
        await shutdown()
        return 1


def main() -> int:
    """Entry point for the smoke test."""
    result = asyncio.run(run_smoke_test())
    return result


if __name__ == "__main__":
    sys.exit(main())