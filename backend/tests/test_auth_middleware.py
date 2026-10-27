"""Auth-header middleware tests (the layer disabled by conftest for others).

Covers the spec rule that missing/malformed credentials yield 401 *before*
body validation — even for a POST with no body at all — plus pass-through
for well-formed headers and CORS preflight immunity.
"""

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app import auth_middleware  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.auth_dep import get_current_user  # noqa: E402

ORIGIN = "http://localhost:5173"


def _client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_missing_header_post_without_body_is_401(monkeypatch) -> None:
    """No body + no credentials: 401, never 422 (no schema leak pre-auth)."""
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().post("/api/v1/agent/analyze")
    assert resp.status_code == 401
    assert "Authorization" in resp.json()["detail"]
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_missing_header_get_is_401(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().get("/api/v1/runs")
    assert resp.status_code == 401


def test_malformed_scheme_is_401(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().post(
        "/api/v1/agent/analyze",
        json={"task": "x"},
        headers={"Authorization": "Token abc.def"},
    )
    assert resp.status_code == 401


def test_empty_bearer_is_401(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().get(
        "/api/v1/runs", headers={"Authorization": "Bearer   "}
    )
    assert resp.status_code == 401


def test_well_formed_header_passes_to_dependency(monkeypatch) -> None:
    """Header shape checked here; token identity still resolved downstream."""
    monkeypatch.setattr(auth_middleware, "enabled", True)
    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: "user-42"
    try:
        resp = _client().get(
            "/api/v1/workspaces", headers={"Authorization": "Bearer whatever"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert all(ws["id"] not in {"local-project", "demo-repo"} for ws in body)
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_public_routes_stay_open(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    c = _client()
    assert c.get("/health").status_code == 200
    assert c.get("/").status_code == 200


def test_cors_preflight_not_blocked_by_auth_gate(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().options(
        "/api/v1/runs",
        headers={
            "Origin": ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == ORIGIN


def test_cors_headers_on_auth_error_responses(monkeypatch) -> None:
    monkeypatch.setattr(auth_middleware, "enabled", True)
    resp = _client().get("/api/v1/runs", headers={"Origin": ORIGIN})
    assert resp.status_code == 401
    assert resp.headers.get("access-control-allow-origin") == ORIGIN


def test_cors_rejects_unknown_origin() -> None:
    resp = _client().get(
        "/health", headers={"Origin": "http://evil.example"}
    )
    assert resp.headers.get("access-control-allow-origin") is None
