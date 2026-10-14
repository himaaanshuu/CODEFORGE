"""API tests for CodeForge AI endpoints.

Covers workspace listing, file tree, file reading (with path/sensitivity
guards), and the analyze endpoint's workspace validation. No LLM calls.
"""

from __future__ import annotations

import os
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.main import PROJECT_ROOT, WORKSPACE_MAPPING, app  # noqa: E402
from backend.auth_dep import get_current_user  # noqa: E402

# Workspace-logic tests focus on routing/paths, not identity. Supabase is
# mocked *in tests only* — auth behaviour itself is covered by test_auth.py.
app.dependency_overrides[get_current_user] = lambda: "test-user-uid"

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_list_workspaces_returns_real_configured_roots() -> None:
    resp = client.get("/api/v1/workspaces")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for ws in data:
        assert ws["id"]
        assert ws["name"]
        assert os.path.isdir(ws["path"])
        assert isinstance(ws["branch"], str)


def test_workspace_tree_lists_project_files() -> None:
    resp = client.get("/api/v1/workspaces/local-project/tree")
    assert resp.status_code == 200
    root = resp.json()
    assert root["type"] == "dir"
    names = {c["name"] for c in root["children"]}
    assert "backend" in names
    assert "frontend" in names
    assert "node_modules" not in names
    assert ".git" not in names


def test_workspace_tree_rejects_unknown_workspace() -> None:
    resp = client.get("/api/v1/workspaces/does-not-exist/tree")
    assert resp.status_code == 404


def test_workspace_tree_depth_is_bounded() -> None:
    resp = client.get("/api/v1/workspaces/local-project/tree", params={"max_depth": 1})
    assert resp.status_code == 200
    for child in resp.json()["children"]:
        if child["type"] == "dir":
            # depth=1: a top-level dir may list files, but no nested directories
            assert all(g.get("type") == "file" for g in child.get("children", []))


def test_file_endpoint_reads_real_file() -> None:
    resp = client.get(
        "/api/v1/workspaces/local-project/file",
        params={"path": "backend/app/main.py"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "backend/app/main.py"
    assert "CodeForge AI" in data["content"]
    assert data["truncated"] is False


def test_file_endpoint_rejects_traversal() -> None:
    resp = client.get(
        "/api/v1/workspaces/local-project/file",
        params={"path": "../../etc/passwd"},
    )
    assert resp.status_code == 400


def test_file_endpoint_rejects_absolute_path() -> None:
    resp = client.get(
        "/api/v1/workspaces/local-project/file",
        params={"path": "/etc/passwd"},
    )
    assert resp.status_code == 400


def test_file_endpoint_rejects_sensitive_files() -> None:
    resp = client.get(
        "/api/v1/workspaces/local-project/file",
        params={"path": ".env"},
    )
    assert resp.status_code == 403


def test_file_endpoint_rejects_unknown_file() -> None:
    resp = client.get(
        "/api/v1/workspaces/local-project/file",
        params={"path": "no/such/file.py"},
    )
    assert resp.status_code == 404


def test_analyze_rejects_unknown_workspace_without_llm_call() -> None:
    resp = client.post(
        "/api/v1/agent/analyze",
        json={"workspace_id": "/definitely/not/a/real/dir", "task": "anything"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert data["status"] == "error"
    # strict allow-list: paths outside WORKSPACE_MAPPING are rejected outright
    assert "Unknown workspace" in data["error"]
    # metric fields still present for the frontend
    assert data["duration_seconds"] == 0.0
    assert data["tokens_used"] == 0


def test_workspace_mapping_points_at_this_project() -> None:
    # Must point at this checkout regardless of the directory name it was
    # cloned into (e.g. "codeforge-ai", "CODEFORGE", ...).
    assert WORKSPACE_MAPPING["local-project"] == str(PROJECT_ROOT)
    assert os.path.isdir(WORKSPACE_MAPPING["local-project"])
    assert os.path.isdir(os.path.join(WORKSPACE_MAPPING["local-project"], "backend"))
    assert os.path.isdir(os.path.join(WORKSPACE_MAPPING["local-project"], "frontend"))


def test_clone_rejects_invalid_owner() -> None:
    resp = client.post(
        "/api/v1/repos/clone",
        json={"owner": "../etc", "name": "passwd"},
    )
    assert resp.status_code == 400
    assert "Invalid repository" in resp.json()["detail"]


def test_clone_rejects_invalid_name() -> None:
    resp = client.post(
        "/api/v1/repos/clone",
        json={"owner": "octocat", "name": "hello/world"},
    )
    assert resp.status_code == 400
    assert "Invalid repository" in resp.json()["detail"]


def test_clone_rejects_empty_fields() -> None:
    resp = client.post("/api/v1/repos/clone", json={"owner": "", "name": ""})
    assert resp.status_code == 400
