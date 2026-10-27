"""API tests for CodeForge AI endpoints.

Covers workspace listing, file tree, file reading (with path/sensitivity
guards), and the analyze endpoint's workspace validation. No LLM calls.
"""

from __future__ import annotations

import os
import subprocess
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from backend.app.main import PROJECT_ROOT, WORKSPACE_MAPPING, WORKSPACE_OWNERS, app  # noqa: E402
from backend.auth_dep import get_current_user  # noqa: E402

# Workspace-logic tests focus on routing/paths, not identity. Supabase is
# mocked *in tests only* — auth behaviour itself is covered by test_auth.py.
app.dependency_overrides[get_current_user] = lambda: "test-user-uid"
WORKSPACE_MAPPING["test-workspace"] = str(PROJECT_ROOT)
WORKSPACE_OWNERS["test-workspace"] = "test-user-uid"

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
    resp = client.get("/api/v1/workspaces/test-workspace/tree")
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
    resp = client.get("/api/v1/workspaces/test-workspace/tree", params={"max_depth": 1})
    assert resp.status_code == 200
    for child in resp.json()["children"]:
        if child["type"] == "dir":
            # depth=1: a top-level dir may list files, but no nested directories
            assert all(g.get("type") == "file" for g in child.get("children", []))


def test_file_endpoint_reads_real_file() -> None:
    resp = client.get(
        "/api/v1/workspaces/test-workspace/file",
        params={"path": "backend/app/main.py"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == "backend/app/main.py"
    assert "CodeForge AI" in data["content"]
    assert data["truncated"] is False


def test_file_endpoint_rejects_traversal() -> None:
    resp = client.get(
        "/api/v1/workspaces/test-workspace/file",
        params={"path": "../../etc/passwd"},
    )
    assert resp.status_code == 400


def test_file_endpoint_rejects_absolute_path() -> None:
    resp = client.get(
        "/api/v1/workspaces/test-workspace/file",
        params={"path": "/etc/passwd"},
    )
    assert resp.status_code == 400


def test_file_endpoint_rejects_sensitive_files() -> None:
    resp = client.get(
        "/api/v1/workspaces/test-workspace/file",
        params={"path": ".env"},
    )
    assert resp.status_code == 403


def test_file_endpoint_rejects_unknown_file() -> None:
    resp = client.get(
        "/api/v1/workspaces/test-workspace/file",
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


def test_analyze_accepts_super_model_label() -> None:
    # A valid model label must not block the request: with an unknown
    # workspace the failure must still be about the workspace, not the model.
    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "workspace_id": "/definitely/not/a/real/dir",
            "task": "anything",
            "model": "Nemotron 3 Super",
        },
    )
    assert resp.status_code == 200
    assert "Unknown workspace" in resp.json()["error"]


def test_analyze_accepts_super_model_id() -> None:
    resp = client.post(
        "/api/v1/agent/analyze",
        json={
            "workspace_id": "/definitely/not/a/real/dir",
            "task": "anything",
            "model": "nvidia/nemotron-3-super-120b-a12b",
        },
    )
    assert resp.status_code == 200
    assert "Unknown workspace" in resp.json()["error"]


def test_analyze_rejects_unknown_model_without_llm_call() -> None:
    # Fail-closed on the model too: rejected before any workspace work or
    # LLM call, so a bad value can never silently run on Ultra.
    resp = client.post(
        "/api/v1/agent/analyze",
        json={"workspace_id": "test-workspace", "task": "anything", "model": "not-a-model"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Unknown model" in data["error"]


def test_application_source_is_not_exposed_as_a_workspace() -> None:
    assert "local-project" not in WORKSPACE_MAPPING
    assert "demo-repo" not in WORKSPACE_MAPPING


def test_workspace_is_hidden_from_another_user() -> None:
    resp = client.get("/api/v1/workspaces/test-workspace/tree")
    assert resp.status_code == 200

    previous = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = lambda: "another-user-uid"
    try:
        assert client.get("/api/v1/workspaces").json() == []
        assert client.get("/api/v1/workspaces/test-workspace/tree").status_code == 404
        assert client.get(
            "/api/v1/workspaces/test-workspace/file", params={"path": "README.md"}
        ).status_code == 404
        assert client.get(
            "/api/v1/workspaces/test-workspace/git/diff",
            params={"files": "README.md"},
        ).status_code == 404
        assert client.post(
            "/api/v1/workspaces/test-workspace/git/publish",
            json={
                "files": ["README.md"],
                "branch_name": "unauthorized",
                "commit_message": "unauthorized",
                "github_token": "test-token",
            },
        ).status_code == 404
        analyze = client.post(
            "/api/v1/agent/analyze",
            json={"workspace_id": "test-workspace", "task": "change README"},
        )
        assert analyze.status_code == 200
        assert "Unknown workspace" in analyze.json()["error"]
    finally:
        app.dependency_overrides[get_current_user] = previous


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


def test_publish_rejects_secret_environment_file(
    tmp_path, monkeypatch
) -> None:
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "https://github.com/octocat/hello-world.git"],
        capture_output=True,
        check=True,
    )
    monkeypatch.setitem(WORKSPACE_MAPPING, "publish-test", str(tmp_path))
    monkeypatch.setitem(WORKSPACE_OWNERS, "publish-test", "test-user-uid")

    resp = client.post(
        "/api/v1/workspaces/publish-test/git/publish",
        json={
            "files": [".env"],
            "branch_name": "test-update",
            "commit_message": "test update",
            "github_token": "never-logged-test-token",
        },
    )

    assert resp.status_code == 400
    assert "Secret environment files" in resp.json()["detail"]


def test_workspace_git_diff_returns_selected_file_diff(tmp_path, monkeypatch) -> None:
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    file_path = tmp_path / "sample.py"
    file_path.write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "sample.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-m", "initial"], check=True)
    file_path.write_text("value = 2\n", encoding="utf-8")
    monkeypatch.setitem(WORKSPACE_MAPPING, "diff-test", str(tmp_path))
    monkeypatch.setitem(WORKSPACE_OWNERS, "diff-test", "test-user-uid")

    resp = client.get(
        "/api/v1/workspaces/diff-test/git/diff",
        params={"files": "sample.py"},
    )

    assert resp.status_code == 200
    assert "-value = 1" in resp.json()["diff"]
    assert "+value = 2" in resp.json()["diff"]
