"""Authentication tests for CodeForge AI.

Covers the Supabase bearer-token dependency end to end:
  • missing / malformed Authorization header → 401
  • invalid / expired / wrong-issuer / wrong-signature token → 401
    (real PyJWT verification with a test-owned secret — no mocks here)
  • unconfigured Supabase backend → 503 (fails closed, never bypasses)
  • valid token → sub extracted and the request succeeds
  • public routes stay reachable without a token

Dependency-level mocking (auth_dep seam) is used only where the test
targets the wiring itself; the crypto path is exercised for real.
"""

from __future__ import annotations

import os
import sys
import time

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import backend.auth_dep as auth_dep  # noqa: E402
from backend.app.main import app as api_app  # noqa: E402
from backend.auth_dep import get_current_user  # noqa: E402

TEST_URL = "https://test-project.supabase.co"
TEST_SECRET = "test-jwt-secret-for-pytest-only"


def _token(
    *,
    secret: str = TEST_SECRET,
    sub: str = "user-123",
    iss: str | None = None,
    exp_offset: int = 3600,
    role: str = "authenticated",
) -> str:
    now = int(time.time())
    claims = {
        "sub": sub,
        "aud": "authenticated",
        "iss": iss or f"{TEST_URL}/auth/v1",
        "iat": now,
        "exp": now + exp_offset,
        "role": role,
        "email": "u@example.com",
    }
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.fixture()
def supabase_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", TEST_URL)
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)


# --- Unit tests of the dependency itself ------------------------------------

app = FastAPI()


@app.get("/protected")
def protected(user_uid: str = Depends(get_current_user)) -> dict:
    return {"uid": user_uid}


client = TestClient(app)


def test_missing_authorization_header_is_401() -> None:
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert "missing or malformed" in resp.json()["detail"]


def test_malformed_authorization_scheme_is_401() -> None:
    resp = client.get("/protected", headers={"Authorization": "Token abc123"})
    assert resp.status_code == 401
    assert "missing or malformed" in resp.json()["detail"]


def test_empty_bearer_token_is_401() -> None:
    resp = client.get("/protected", headers={"Authorization": "Bearer    "})
    assert resp.status_code == 401
    assert "empty token" in resp.json()["detail"]


def test_dependency_error_passthrough(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 503 raised by the verifier propagates (config errors stay 503)."""
    def fake_verify(token: str) -> dict:
        raise HTTPException(status_code=503, detail="Supabase auth is not configured.")

    monkeypatch.setattr(auth_dep, "verify_supabase_token", fake_verify)
    resp = client.get("/protected", headers={"Authorization": "Bearer any"})
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"]


def test_token_without_sub_claim_is_401(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_dep, "verify_supabase_token", lambda token: {})
    resp = client.get("/protected", headers={"Authorization": "Bearer good-token"})
    assert resp.status_code == 401
    assert "no sub claim" in resp.json()["detail"]


# --- Real cryptographic verification (test-owned secret, no mocks) -----------


def test_valid_signed_token_authenticates(supabase_env) -> None:
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_token()}"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"uid": "user-123"}


def test_wrong_signature_is_401(supabase_env) -> None:
    resp = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {_token(secret='attacker-secret')}"},
    )
    assert resp.status_code == 401
    assert "Unauthorized" in resp.json()["detail"]


def test_expired_token_is_401(supabase_env) -> None:
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_token(exp_offset=-60)}"}
    )
    assert resp.status_code == 401


def test_wrong_issuer_is_401(supabase_env) -> None:
    resp = client.get(
        "/protected",
        headers={
            "Authorization": f"Bearer {_token(iss='https://evil.supabase.co/auth/v1')}"
        },
    )
    assert resp.status_code == 401


def test_wrong_audience_is_401(supabase_env) -> None:
    now = int(time.time())
    forged = jwt.encode(
        {
            "sub": "user-123",
            "aud": "not-authenticated",
            "iss": f"{TEST_URL}/auth/v1",
            "iat": now,
            "exp": now + 3600,
        },
        TEST_SECRET,
        algorithm="HS256",
    )
    resp = client.get("/protected", headers={"Authorization": f"Bearer {forged}"})
    assert resp.status_code == 401


def test_non_authenticated_role_is_401(supabase_env) -> None:
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_token(role='anon')}"}
    )
    assert resp.status_code == 401
    assert "role" in resp.json()["detail"]


def test_unconfigured_supabase_is_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unconfigured Supabase fails closed — never a silent bypass."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {_token()}"})
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"]


# --- ES256 (current Supabase default: asymmetric project keys via JWKS) ------


def _es256_token(private_key, *, sub: str = "user-123", exp_offset: int = 3600) -> str:
    now = int(time.time())
    claims = {
        "sub": sub,
        "aud": "authenticated",
        "iss": f"{TEST_URL}/auth/v1",
        "iat": now,
        "exp": now + exp_offset,
        "role": "authenticated",
        "email": "u@example.com",
    }
    return jwt.encode(claims, private_key, algorithm="ES256", headers={"kid": "test-kid"})


@pytest.fixture()
def es256_env(supabase_env, monkeypatch: pytest.MonkeyPatch):
    """Supabase env + a local EC P-256 keypair standing in for the JWKS."""
    from types import SimpleNamespace

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    import backend.supabase_auth as supabase_auth

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    class _StubJWKS:
        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            return SimpleNamespace(key=public_pem)

    monkeypatch.setattr(supabase_auth, "_jwks_client", lambda url: _StubJWKS())
    return private_key


def test_valid_es256_token_authenticates(es256_env) -> None:
    """Real Supabase access tokens (ES256 + JWKS) pass verification."""
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_es256_token(es256_env)}"}
    )
    assert resp.status_code == 200
    assert resp.json() == {"uid": "user-123"}


def test_es256_wrong_signing_key_is_401(es256_env, monkeypatch: pytest.MonkeyPatch) -> None:
    """An ES256 token signed by a key not in the JWKS is rejected."""
    from types import SimpleNamespace

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    import backend.supabase_auth as supabase_auth

    attacker_key = ec.generate_private_key(ec.SECP256R1())
    attacker_pem = attacker_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    class _AttackerJWKS:
        def get_signing_key_from_jwt(self, token: str) -> SimpleNamespace:
            return SimpleNamespace(key=attacker_pem)

    monkeypatch.setattr(supabase_auth, "_jwks_client", lambda url: _AttackerJWKS())
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_es256_token(es256_env)}"}
    )
    assert resp.status_code == 401
    assert "Unauthorized" in resp.json()["detail"]


def test_disallowed_algorithm_is_401(supabase_env) -> None:
    """Algorithms outside {HS256, ES256, RS256} are rejected outright."""
    resp = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {_tokenHS384()}"},
    )
    assert resp.status_code == 401
    assert "not allowed" in resp.json()["detail"]


def _tokenHS384() -> str:
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "user-123",
            "aud": "authenticated",
            "iss": f"{TEST_URL}/auth/v1",
            "iat": now,
            "exp": now + 3600,
            "role": "authenticated",
        },
        TEST_SECRET,
        algorithm="HS384",
    )


def test_jwks_unavailable_is_503(es256_env, monkeypatch: pytest.MonkeyPatch) -> None:
    """If the project JWKS cannot be fetched, verification fails closed (503)."""
    from jwt import PyJWKClientError

    import backend.supabase_auth as supabase_auth

    def _broken(url: str):
        class _Broken:
            def get_signing_key_from_jwt(self, token: str):
                raise PyJWKClientError("connection refused")

        return _Broken()

    monkeypatch.setattr(supabase_auth, "_jwks_client", _broken)
    resp = client.get(
        "/protected", headers={"Authorization": f"Bearer {_es256_token(es256_env)}"}
    )
    assert resp.status_code == 503
    assert "JWKS unavailable" in resp.json()["detail"]


# --- Wiring: the real API app ----------------------------------------------


def test_api_requires_token_on_protected_routes() -> None:
    """The workspace API rejects requests with no credentials at all.

    Clears any dependency overrides first — test_api.py overrides identity
    for its own workspace-logic cases.
    """
    saved = dict(api_app.dependency_overrides)
    api_app.dependency_overrides.clear()
    try:
        c = TestClient(api_app)
        assert c.get("/api/v1/workspaces").status_code == 401
        assert c.get("/api/v1/workspaces/local-project/tree").status_code == 401
        assert c.get("/api/v1/workspaces/local-project/file?path=README.md").status_code == 401
        assert c.post("/api/v1/agent/analyze", json={"task": "x"}).status_code == 401
        assert c.post("/api/v1/llm/generate", json={"prompt": "hi"}).status_code == 401
    finally:
        api_app.dependency_overrides.update(saved)


def test_public_routes_need_no_token() -> None:
    c = TestClient(api_app)
    assert c.get("/").status_code == 200
    assert c.get("/health").status_code == 200
