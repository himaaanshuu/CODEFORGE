# CodeForge AI — Supabase (Postgres via PostgREST) persistence layer
# ===================================================================
# Server-side only. Every row carries `owner_uid`; reads are always
# filtered by the uid from the verified Supabase token. Clients have no
# direct database access at all: RLS is enabled with NO policies (see
# supabase/migrations/0001_init.sql) — only the service-role key used
# here can read/write.
#
# Tables:
#   agent_runs        one agent run: status, task, metrics, plan, files
#   agent_run_events  event timeline entries (owner_uid + run_id)
#   usage_records     token/time usage rows (owner_uid + run_id)
#
# Environment (Dashboard → Project Settings → API):
#   SUPABASE_URL              e.g. https://<ref>.supabase.co
#   SUPABASE_SERVICE_ROLE_KEY secret service-role key (server only!)
#
# Storage is optional at runtime: without configuration these endpoints
# fail closed with HTTP 503 — never a silent bypass.

from __future__ import annotations

import os
import time
import uuid
from typing import Any, Optional

import httpx
from fastapi import HTTPException

RUNS = "agent_runs"
RUN_EVENTS = "agent_run_events"
USAGE_RECORDS = "usage_records"

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10

_REQUEST_TIMEOUT = 15.0


def _config() -> tuple[str, str]:
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    return url, key


def _db() -> tuple[str, dict[str, str]]:
    """(base URL, headers) for PostgREST, or HTTP 503 when not configured."""
    url, key = _config()
    if not url or not key:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase is not configured on this server: set SUPABASE_URL "
                "and SUPABASE_SERVICE_ROLE_KEY (Dashboard → Project Settings → API)."
            ),
        )
    return (
        f"{url}/rest/v1",
        {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )


def _request(
    method: str,
    table: str,
    *,
    params: Optional[dict[str, str]] = None,
    json_body: Optional[dict[str, Any]] = None,
) -> Any:
    """One PostgREST call. Returns parsed JSON, or raises 503 on any error.

    Fail closed: transport problems and database errors (including a
    missing migration) surface as explicit 503s, never as silent skips.
    """
    base, headers = _db()
    try:
        resp = httpx.request(
            method,
            f"{base}/{table}",
            params=params,
            json=json_body,
            headers=headers,
            timeout=_REQUEST_TIMEOUT,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Supabase database unreachable: {exc.__class__.__name__}",
        ) from exc

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=503,
            detail=f"Supabase database error ({resp.status_code}): {resp.text[:300]}",
        )
    if resp.status_code == 204 or not resp.content:
        return None
    return resp.json()


def _now() -> float:
    return time.time()


def new_run_id() -> str:
    return uuid.uuid4().hex


def start_run(
    uid: str,
    *,
    task: str,
    workspace_id: str,
    run_id: Optional[str] = None,
) -> str:
    """Create a RUNNING run row owned by `uid`. Returns the run id."""
    run_id = run_id or new_run_id()
    now = _now()
    _request(
        "POST",
        RUNS,
        json_body={
            "id": run_id,
            "owner_uid": uid,
            "task": task,
            "workspace_id": workspace_id,
            "status": "RUNNING",
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error": None,
            "summary": "",
            "metrics": {},
            "plan": [],
            "files_inspected": [],
            "files_changed": [],
            "diff_summary": "",
            "observation_count": 0,
        },
    )
    return run_id


def finish_run(
    run_id: str,
    uid: str,
    *,
    status: str,
    summary: str,
    error: Optional[str],
    metrics: dict[str, Any],
    plan: list[str],
    files_inspected: list[str],
    files_changed: list[str],
    diff_summary: str,
    observations: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> None:
    """Complete a run with real results and write its usage record.

    Ownership is verified first (404 unknown, 403 another user's run) so no
    status change, event, or usage row is ever written for a run the caller
    does not own.
    """
    if status not in ("COMPLETED", "FAILED"):
        raise ValueError(f"invalid terminal status: {status}")
    get_run(uid, run_id)  # ownership check before any write
    now = _now()

    _request(
        "PATCH",
        RUNS,
        params={"id": f"eq.{run_id}", "owner_uid": f"eq.{uid}"},
        json_body={
            "status": status,
            "updated_at": now,
            "completed_at": now,
            "summary": summary,
            "error": error,
            "metrics": metrics,
            "plan": plan,
            "files_inspected": files_inspected,
            "files_changed": files_changed,
            "diff_summary": diff_summary,
            "observation_count": len(observations),
        },
    )

    # Event timeline (server-written; clients cannot create these).
    for i, event in enumerate(events):
        # Merge the event's top-level fields (tool_name, observation, ...) into
        # the data column so API consumers get the full payload, not just type.
        event_data = dict(event.get("data") or {})
        for key, value in event.items():
            if key not in ("type", "timestamp", "data"):
                event_data.setdefault(key, value)
        _request(
            "POST",
            RUN_EVENTS,
            json_body={
                "id": new_run_id(),
                "owner_uid": uid,
                "run_id": run_id,
                "seq": float(i),
                "type": event.get("type", ""),
                "timestamp": float(event.get("timestamp", 0.0)),
                "data": event_data,
                "created_at": now,
            },
        )

    # Usage record — the trusted token/time accounting row.
    _request(
        "POST",
        USAGE_RECORDS,
        json_body={
            "id": new_run_id(),
            "owner_uid": uid,
            "run_id": run_id,
            "tokens_used": int(metrics.get("tokensUsed", 0)),
            "duration_seconds": float(metrics.get("durationSeconds", 0.0)),
            "model": metrics.get("model", ""),
            "iterations": int(metrics.get("iterations", 0)),
            "repair_attempts": int(metrics.get("repairAttempts", 0)),
            "created_at": now,
        },
    )


def get_run(uid: str, run_id: str) -> dict[str, Any]:
    """Fetch one run; 404 when missing, 403 when owned by another user."""
    rows = _request("GET", RUNS, params={"id": f"eq.{run_id}", "limit": "1"})
    if not rows:
        raise HTTPException(status_code=404, detail="Run not found")
    data = dict(rows[0])
    if data.get("owner_uid") != uid:
        # Do not leak existence of other users' runs: 404 would be even
        # stricter; 403 documents the ownership rule explicitly.
        raise HTTPException(status_code=403, detail="Forbidden: not your run")
    return data


def list_runs(
    uid: str,
    *,
    limit: int = DEFAULT_PAGE_SIZE,
    cursor: Optional[float] = None,
) -> dict[str, Any]:
    """Newest-first page of the caller's runs (always owner_uid-filtered)."""
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    params: dict[str, str] = {
        "owner_uid": f"eq.{uid}",
        "order": "created_at.desc",
        "limit": str(limit),
    }
    if cursor is not None:
        params["created_at"] = f"lt.{cursor}"

    rows = _request("GET", RUNS, params=params) or []

    next_cursor: Optional[float] = None
    if len(rows) == limit and rows:
        next_cursor = rows[-1].get("created_at")

    return {"runs": rows, "nextCursor": next_cursor}


def list_run_events(
    uid: str,
    run_id: str,
    *,
    limit: int = DEFAULT_PAGE_SIZE,
    cursor: Optional[float] = None,
) -> dict[str, Any]:
    """Paginated event timeline of one of the caller's runs."""
    get_run(uid, run_id)  # ownership check first
    limit = max(1, min(limit, MAX_PAGE_SIZE))
    params: dict[str, str] = {
        "run_id": f"eq.{run_id}",
        "order": "seq.asc",
        "limit": str(limit),
    }
    if cursor is not None:
        params["seq"] = f"gt.{cursor}"

    rows = _request("GET", RUN_EVENTS, params=params) or []

    next_cursor: Optional[float] = None
    if len(rows) == limit and rows:
        next_cursor = rows[-1].get("seq")

    return {"events": rows, "nextCursor": next_cursor}
