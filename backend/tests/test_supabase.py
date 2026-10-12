"""Supabase persistence tests (PostgREST + real schema + real JWT seams).

Seams (mocked in tests only):
  • supabase_service._request → in-memory fake PostgREST store
Covered:
  • run rows are created with owner_uid and real status transitions
  • finish_run is owner-scoped — a run can only be finished by its owner
  • cross-user access is rejected (403) on runs and event timelines
  • list queries only ever return the caller's own runs (cursor pagination)
  • usage records capture real metrics written server-side
  • API wiring requires a verified token
  • unconfigured Supabase → 503 (fail closed, no silent bypass)
  • migration SQL: RLS enabled, no client-facing policies (deny-all)
"""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import backend.supabase_service as store  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.auth_dep import get_current_user  # noqa: E402

# --- In-memory fake PostgREST (test double for the Supabase REST API) -------


def _eq(row_val: Any, operand: str) -> bool:
    return str(row_val) == operand


def _num(row_val: Any, operand: str, op: str) -> bool:
    if row_val is None:
        return False
    left, right = float(row_val), float(operand)
    return left < right if op == "lt" else left > right


class FakeRest:
    """Implements the exact `_request` contract used by supabase_service."""

    def __init__(self) -> None:
        self.tables: dict[str, dict[str, dict]] = {
            store.RUNS: {},
            store.RUN_EVENTS: {},
            store.USAGE_RECORDS: {},
        }
        self.last_params: Optional[dict[str, str]] = None

    def __call__(
        self,
        method: str,
        table: str,
        *,
        params: Optional[dict[str, str]] = None,
        json_body: Optional[dict[str, Any]] = None,
    ) -> Any:
        params = dict(params or {})
        self.last_params = params

        if method == "POST":
            row = dict(json_body or {})
            self.tables[table][row["id"]] = row
            return None

        if method == "PATCH":
            matched = self._match(table, params)
            for row in matched:
                row.update(json_body or {})
            return None

        # GET
        matched = self._match(table, params)
        order = params.get("order")
        if order:
            col, _, direction = order.partition(".")
            matched.sort(
                key=lambda r: (r.get(col) is None, r.get(col)),
                reverse=direction == "desc",
            )
        if "limit" in params:
            matched = matched[: int(params["limit"])]
        return [dict(r) for r in matched]

    def _match(self, table: str, params: dict[str, str]) -> list[dict]:
        out = []
        for row in self.tables[table].values():
            ok = True
            for col, expr in params.items():
                if col in ("order", "limit"):
                    continue
                op, _, operand = expr.partition(".")
                if op == "eq":
                    ok = _eq(row.get(col), operand)
                elif op in ("lt", "gt"):
                    ok = _num(row.get(col), operand, op)
                else:
                    raise AssertionError(f"fake does not support operator {op!r}")
                if not ok:
                    break
            if ok:
                out.append(row)
        return out


@pytest.fixture()
def fake_rest(monkeypatch: pytest.MonkeyPatch) -> FakeRest:
    fake = FakeRest()
    monkeypatch.setattr(store, "_request", fake)
    return fake


# --- Service-level behaviour ------------------------------------------------


def test_start_run_creates_running_row_with_owner(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="do things", workspace_id="local-project")
    row = fake_rest.tables[store.RUNS][run_id]
    assert row["owner_uid"] == "alice"
    assert row["status"] == "RUNNING"
    assert row["task"] == "do things"
    assert row["created_at"] <= row["updated_at"]


def test_finish_run_records_real_metrics_and_usage(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="t", workspace_id="local-project")
    store.finish_run(
        run_id,
        "alice",
        status="COMPLETED",
        summary="all good",
        error=None,
        metrics={
            "tokensUsed": 4210,
            "durationSeconds": 12.5,
            "model": "nvidia/Nemotron-3-Ultra-550b-a55b",
            "iterations": 3,
            "maxIterations": 10,
            "filesChanged": 2,
            "repairAttempts": 0,
            "toolsUsed": ["list_files", "read_file"],
        },
        plan=["step 1"],
        files_inspected=["a.py"],
        files_changed=["a.py", "b.py"],
        diff_summary="diff --git a/a.py b/a.py",
        observations=[{"tool_name": "read_file"}],
        events=[{"type": "agent_started", "timestamp": 1.0, "data": {}}],
    )

    row = fake_rest.tables[store.RUNS][run_id]
    assert row["status"] == "COMPLETED"
    assert row["metrics"]["tokensUsed"] == 4210
    assert row["completed_at"] is not None
    assert row["error"] is None

    usage = list(fake_rest.tables[store.USAGE_RECORDS].values())
    assert len(usage) == 1
    assert usage[0]["tokens_used"] == 4210
    assert usage[0]["owner_uid"] == "alice"
    assert usage[0]["run_id"] == run_id

    events = list(fake_rest.tables[store.RUN_EVENTS].values())
    assert len(events) == 1
    assert events[0]["type"] == "agent_started"
    assert events[0]["owner_uid"] == "alice"
    assert events[0]["seq"] == 0.0


def test_finish_run_is_owner_scoped(fake_rest: FakeRest) -> None:
    """A different user cannot finish (or corrupt) someone else's run."""
    run_id = store.start_run("alice", task="t", workspace_id="local-project")
    with pytest.raises(Exception) as excinfo:
        store.finish_run(
            run_id,
            "mallory",  # wrong owner → rejected before any write
            status="FAILED",
            summary="",
            error="hacked",
            metrics={},
            plan=[],
            files_inspected=[],
            files_changed=[],
            diff_summary="",
            observations=[],
            events=[],
        )
    assert getattr(excinfo.value, "status_code", None) == 403
    row = fake_rest.tables[store.RUNS][run_id]
    assert row["status"] == "RUNNING"  # unchanged
    assert row["error"] is None
    assert fake_rest.tables[store.USAGE_RECORDS] == {}
    assert fake_rest.tables[store.RUN_EVENTS] == {}


def test_finish_run_rejects_non_terminal_status(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="t", workspace_id="local-project")
    with pytest.raises(ValueError):
        store.finish_run(
            run_id,
            "alice",
            status="RUNNING",
            summary="",
            error=None,
            metrics={},
            plan=[],
            files_inspected=[],
            files_changed=[],
            diff_summary="",
            observations=[],
            events=[],
        )


def test_get_run_cross_user_is_403(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="secret work", workspace_id="local-project")
    with pytest.raises(Exception) as excinfo:
        store.get_run("bob", run_id)
    assert getattr(excinfo.value, "status_code", None) == 403


def test_get_run_unknown_is_404(fake_rest: FakeRest) -> None:
    with pytest.raises(Exception) as excinfo:
        store.get_run("alice", "nope")
    assert getattr(excinfo.value, "status_code", None) == 404


def test_get_run_owner_sees_own_data(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="mine", workspace_id="local-project")
    run = store.get_run("alice", run_id)
    assert run["id"] == run_id
    assert run["task"] == "mine"


def test_list_runs_returns_only_own_runs(fake_rest: FakeRest) -> None:
    store.start_run("alice", task="alice-1", workspace_id="local-project")
    store.start_run("bob", task="bob-1", workspace_id="local-project")
    store.start_run("alice", task="alice-2", workspace_id="local-project")

    page = store.list_runs("alice", limit=10)
    tasks = {r["task"] for r in page["runs"]}
    assert tasks == {"alice-1", "alice-2"}
    assert all(r["owner_uid"] == "alice" for r in page["runs"])
    assert page["nextCursor"] is None  # fewer than limit
    # The query itself is owner-scoped:
    assert fake_rest.last_params is not None
    assert fake_rest.last_params.get("owner_uid") == "eq.alice"


def test_list_runs_paginates_with_cursor(fake_rest: FakeRest) -> None:
    for i in range(3):
        run_id = store.start_run("alice", task=f"t{i}", workspace_id="local-project")
        fake_rest.tables[store.RUNS][run_id]["created_at"] = 1000.0 + i

    page1 = store.list_runs("alice", limit=2)
    assert len(page1["runs"]) == 2
    assert page1["nextCursor"] is not None

    page2 = store.list_runs("alice", limit=2, cursor=page1["nextCursor"])
    assert len(page2["runs"]) == 1
    assert page2["runs"][0]["task"] == "t0"  # oldest is last


def test_run_events_require_ownership(fake_rest: FakeRest) -> None:
    run_id = store.start_run("alice", task="t", workspace_id="local-project")
    store.finish_run(
        run_id,
        "alice",
        status="COMPLETED",
        summary="",
        error=None,
        metrics={"tokensUsed": 1, "durationSeconds": 0.1, "model": "m",
                 "iterations": 1, "maxIterations": 10, "filesChanged": 0,
                 "repairAttempts": 0, "toolsUsed": []},
        plan=[],
        files_inspected=[],
        files_changed=[],
        diff_summary="",
        observations=[],
        events=[{"type": "agent_started", "timestamp": 1.0, "data": {}}],
    )

    with pytest.raises(Exception) as excinfo:
        store.list_run_events("bob", run_id)
    assert getattr(excinfo.value, "status_code", None) == 403

    page = store.list_run_events("alice", run_id)
    assert len(page["events"]) == 1


def test_unconfigured_storage_is_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No Supabase config → explicit 503, never a silent bypass."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    with pytest.raises(Exception) as excinfo:
        store.list_runs("alice")
    assert getattr(excinfo.value, "status_code", None) == 503
    assert "not configured" in str(excinfo.value.detail)


# --- API wiring (auth + service) -------------------------------------------


def test_runs_api_requires_token() -> None:
    saved = dict(app.dependency_overrides)
    app.dependency_overrides.clear()
    try:
        c = TestClient(app)
        assert c.get("/api/v1/runs").status_code == 401
        assert c.get("/api/v1/runs/some-id").status_code == 401
        assert c.post("/api/v1/runs", json={"task": "x"}).status_code == 401
    finally:
        app.dependency_overrides.update(saved)


def test_runs_api_isolated_per_user(fake_rest: FakeRest) -> None:
    alice_run = store.start_run("alice", task="alice work", workspace_id="local-project")
    store.start_run("bob", task="bob work", workspace_id="local-project")

    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: "alice"
    try:
        c = TestClient(app)
        listing = c.get("/api/v1/runs")
        assert listing.status_code == 200
        runs = listing.json()["runs"]
        assert {r["task"] for r in runs} == {"alice work"}

        assert c.get(f"/api/v1/runs/{alice_run}").status_code == 200

        app.dependency_overrides[get_current_user] = lambda: "mallory"
        forbidden = c.get(f"/api/v1/runs/{alice_run}")
        assert forbidden.status_code == 403
        assert c.get("/api/v1/runs").json()["runs"] == []
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_unknown_workspace_is_rejected_without_recording(fake_rest: FakeRest) -> None:
    """workspace_id outside the allow-list → 400, and no run is created."""
    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: "alice"
    try:
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.post(
            "/api/v1/runs",
            json={"workspace_id": "/definitely/not/a/dir", "task": "x"},
        )
        assert resp.status_code == 400
        assert "Unknown workspace" in resp.json()["detail"]
        assert fake_rest.tables[store.RUNS] == {}
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


def test_failed_run_is_recorded_without_llm_call(
    fake_rest: FakeRest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crashing agent task fails the endpoint; the failure itself is persisted."""
    import backend.app.agent.agent as agent_mod

    async def _boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("agent exploded")

    monkeypatch.setattr(agent_mod, "run_agent_task", _boom)
    previous = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides[get_current_user] = lambda: "alice"
    try:
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.post(
            "/api/v1/runs",
            json={"workspace_id": "local-project", "task": "x"},
        )
        assert resp.status_code == 500
        runs = list(fake_rest.tables[store.RUNS].values())
        assert len(runs) == 1
        assert runs[0]["status"] == "FAILED"
        assert "agent exploded" in (runs[0]["error"] or "")
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:
            app.dependency_overrides[get_current_user] = previous


# --- Security: migration SQL (deny-all for clients) -------------------------


def _migration_sql() -> str:
    root = os.path.join(os.path.dirname(__file__), "..", "..")
    path = os.path.join(root, "supabase", "migrations", "0001_init.sql")
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def test_migration_defines_all_tables() -> None:
    sql = _migration_sql()
    for table in ("agent_runs", "agent_run_events", "usage_records"):
        assert f"create table if not exists {table}" in sql


def test_migration_enables_rls_with_no_client_policies() -> None:
    sql = _migration_sql()
    low = sql.lower()
    for table in ("agent_runs", "agent_run_events", "usage_records"):
        assert f"alter table {table} enable row level security" in low
    # No policy grants anything to anon/authenticated — service role only:
    assert "create policy" not in low
    assert "to authenticated" not in low
    assert "to anon" not in low
