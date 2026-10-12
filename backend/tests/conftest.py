"""Shared pytest fixtures for the CodeForge backend.

Auth/storage seams are mocked in tests only — this autouse
fixture turns off the pre-routing Authorization-header middleware so the
existing suite authenticates through `app.dependency_overrides` (the seam
used by every test file). Tests that target the middleware itself re-enable
it with monkeypatch inside the test.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _auth_middleware_disabled():
    from backend.app import auth_middleware

    previous = auth_middleware.enabled
    auth_middleware.enabled = False
    yield
    auth_middleware.enabled = previous
