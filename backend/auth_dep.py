# CodeForge AI — FastAPI Supabase authentication dependency
# ==========================================================
# Extracts and verifies a Supabase access token from the
# ``Authorization: Bearer <token>`` header and returns the user id
# (the token's ``sub`` claim — the Supabase Auth user UUID).
#
# Usage:
#   @app.get("/protected")
#   def handler(user_uid: str = Depends(get_current_user)): ...
#
# Raises ``HTTPException(401)`` for missing/malformed/invalid tokens and
# ``HTTPException(503)`` when Supabase auth is not configured (fail closed).

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .supabase_auth import verify_supabase_token


def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
) -> str:
    """Verify the bearer token and return the Supabase user id.

    Authorisation (ownership of a specific resource) stays in the route
    handler so ownership logic lives close to the data.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: missing or malformed Authorization header",
        )

    token = authorization[len("Bearer "):].strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: empty token",
        )

    try:
        user = verify_supabase_token(token)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unauthorized: {exc}",
        ) from exc

    uid = user.get("sub") if isinstance(user, dict) else None
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: token has no sub claim",
        )
    return str(uid)
