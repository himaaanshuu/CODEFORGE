# CodeForge AI — pre-routing Authorization header enforcement
# =============================================================
# Spec: protected routes must return 401 for missing/malformed credentials —
# *before* anything else runs. FastAPI validates the request body before
# dependencies, so without this middleware an unauthenticated POST with a bad
# body would surface 422 (schema details leaked pre-auth). This middleware
# rejects requests under /api/v1/ that lack a well-formed `Bearer <token>`
# header before routing/body parsing. Token *verification* (invalid/expired →
# 401, unconfigured Supabase → 503) still happens in `auth_dep.get_current_user`.
#
# Tests disable this layer and mock authentication at the dependency level
# (`app.dependency_overrides`), like every other auth seam.
# ============================================================================

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi.responses import JSONResponse

PROTECTED_PREFIX = "/api/v1/"

# Flipped off by backend/tests/conftest.py for the test suite.
enabled = True


async def auth_header_middleware(
    request, call_next: Callable[..., Awaitable[object]]
) -> object:
    """401 early for protected paths without a well-formed Bearer header."""
    if (
        enabled
        and request.method != "OPTIONS"
        and request.url.path.startswith(PROTECTED_PREFIX)
    ):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Not authenticated: missing or malformed Authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
    return await call_next(request)
