# CodeForge AI — Supabase Auth verification
# ===========================================
# Environment (Supabase Dashboard → Project Settings → API):
#   SUPABASE_URL             e.g. https://<ref>.supabase.co  (required)
#   SUPABASE_JWT_SECRET      HS256 signing secret           (required)
#
# Verifies Supabase access tokens from `Authorization: Bearer <token>`:
#   - HS256  → signature checked against SUPABASE_JWT_SECRET (legacy)
#   - ES256/RS256 → signature checked against the project JWKS at
#     <SUPABASE_URL>/auth/v1/.well-known/jwks.json (current default:
#     new Supabase projects sign access tokens with an ephemeral EC key)
# Claims: `iss` = <SUPABASE_URL>/auth/v1, `aud` = authenticated,
# required exp/sub/iss/aud; role must be `authenticated` when present.
#
# Fails closed: unconfigured server → HTTP 503 with an explicit config
# error (never a silent bypass); JWKS unreachable → 503; invalid/
# expired/forged/disallowed-alg token → 401. No mock tokens, no skip paths.

from __future__ import annotations

import os
from typing import Any

import jwt
from fastapi import HTTPException
from jwt import PyJWKClient, PyJWKClientError

_ALLOWED_ASYMMETRIC_ALGS = ("ES256", "RS256")


def _config() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    secret = os.getenv("SUPABASE_JWT_SECRET", "").strip()
    return url, secret


def _jwks_client(url: str) -> PyJWKClient:
    """Cached JWKS client for the project's asymmetric signing keys."""
    return PyJWKClient(
        f"{url}/auth/v1/.well-known/jwks.json",
        cache_jwk_set=True,
        lifespan=300,
    )


def supabase_auth_status() -> str:
    """'configured' when token verification can run, else 'not_configured'."""
    url, secret = _config()
    return "configured" if url and secret else "not_configured"


def verify_supabase_token(token: str) -> dict[str, Any]:
    """Cryptographically verify a Supabase access token.

    Returns the decoded claims dict (sub, email, user_metadata, ...).

    Raises ``HTTPException(503)`` when Supabase auth is not configured
    or the project JWKS cannot be fetched (fails closed) and
    ``HTTPException(401)`` for missing/malformed/expired/forged tokens
    or disallowed algorithms.
    """
    url, secret = _config()
    if not url or not secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase auth is not configured on this server: set "
                "SUPABASE_URL and SUPABASE_JWT_SECRET (Dashboard → "
                "Project Settings → API)."
            ),
        )

    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail=f"Unauthorized: {exc}") from exc

    alg = header.get("alg", "")
    options = {"require": ["exp", "sub", "iss", "aud"]}
    audience = "authenticated"
    issuer = f"{url}/auth/v1"

    try:
        if alg == "HS256":
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience=audience,
                issuer=issuer,
                options=options,
            )
        elif alg in _ALLOWED_ASYMMETRIC_ALGS:
            signing_key = _jwks_client(url).get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=[alg],
                audience=audience,
                issuer=issuer,
                options=options,
            )
        else:
            raise HTTPException(
                status_code=401,
                detail=f"Unauthorized: token alg '{alg}' is not allowed",
            )
    except PyJWKClientError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Supabase JWKS unavailable, cannot verify token: {exc}",
        ) from exc
    except jwt.PyJWTError as exc:  # invalid signature/claims/expired/forged
        raise HTTPException(status_code=401, detail=f"Unauthorized: {exc}") from exc

    role = claims.get("role")
    if role is not None and role != "authenticated":
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: token role is not 'authenticated'",
        )
    return claims
