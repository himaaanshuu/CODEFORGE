"""CodeForge AI FastAPI backend.

Public routes (`/`, `/health`) stay open. API routes under `/api/v1` are
protected by Supabase access-token verification (see `backend/auth_dep.py`).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load backend/.env before any module reads environment configuration.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .. import supabase_service as store
from ..auth_dep import get_current_user

app = FastAPI(
    title="CodeForge AI",
    description="Autonomous AI software engineering agent",
    version="0.1.0",
)

# --- Middleware ------------------------------------------------------------
# Registration order matters: the last `add_middleware` call is outermost.
# 1. Auth-header gate (inner): 401 before routing/body parsing on /api/v1/*.
# 2. CORS (outer): every response — including middleware 401s/503s — carries
#    CORS headers so the browser can read them.
from .auth_middleware import auth_header_middleware  # noqa: E402

app.middleware("http")(auth_header_middleware)

from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

_FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)

# --- Workspace configuration ---------------------------------------------
# The single local workspace root the agent is allowed to read/modify.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_MAPPING: dict[str, str] = {
    "local-project": str(PROJECT_ROOT),
    "demo-repo": str(PROJECT_ROOT),
}

# Directories never listed in the file tree.
_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".idea",
    ".vscode",
    ".eggs",
    ".turbo",
    ".cache",
}

_SKIP_FILES = {".DS_Store", "Thumbs.db"}

# Paths the file endpoint refuses to return (secrets / credentials).
_SENSITIVE_SUFFIXES = (".pem", ".p12", ".pfx", ".env")
_SENSITIVE_NAMES = {
    "id_rsa",
    "id_ed25519",
    "id_dsa",
    "credentials.json",
    "service_account.json",
}
_SENSITIVE_SUBSTRINGS = (
    "service_account",
    "secret_key",
    "private_key",
    "api_key",
    "secret_token",
)

_TREE_NODE_BUDGET = 1500
_FILE_MAX_BYTES = 200_000


def _error_response(status_code: int, detail: str) -> JSONResponse:
    """Consistent JSON error body for API failures."""
    return JSONResponse(status_code=status_code, content={"detail": detail})


def _git_branch(root: Path) -> str:
    """Best-effort current git branch name of a workspace root."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _resolve_workspace(workspace_id: str) -> Path | None:
    root = WORKSPACE_MAPPING.get(workspace_id)
    if root is None:
        return None
    path = Path(root)
    return path if path.is_dir() else None


def _build_tree(root: Path, rel: str, depth: int, max_depth: int, budget: list[int]) -> dict:
    """Recursively build a JSON file tree, bounded by depth and node budget."""
    entry: dict = {
        "name": root.name or str(root),
        "path": rel,
        "type": "dir",
        "children": [],
    }
    if depth >= max_depth or budget[0] <= 0:
        return entry

    try:
        children = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except OSError:
        return entry

    for child in children:
        if budget[0] <= 0:
            break
        if child.name in _SKIP_FILES:
            continue
        child_rel = f"{rel}/{child.name}" if rel else child.name
        if child.is_dir():
            if child.name in _SKIP_DIRS or child.name.endswith(".egg-info"):
                continue
            budget[0] -= 1
            entry["children"].append(
                _build_tree(child, child_rel, depth + 1, max_depth, budget)
            )
        elif child.is_file():
            budget[0] -= 1
            entry["children"].append(
                {"name": child.name, "path": child_rel, "type": "file"}
            )
    return entry


def _is_sensitive(path: str) -> bool:
    """True when a workspace-relative path looks like a secret file."""
    lowered = path.lower()
    name = os.path.basename(lowered)
    # .env.example style files carry no secrets.
    if name.startswith(".env.") and name.endswith((".example", ".sample", ".template")):
        return False
    if name.endswith(_SENSITIVE_SUFFIXES):
        return True
    if name in _SENSITIVE_NAMES:
        return True
    return any(marker in lowered for marker in _SENSITIVE_SUBSTRINGS)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CodeForge AI is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "message": "CodeForge AI is running"}


class GenerateRequest(BaseModel):
    prompt: str
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    top_p: float = 1.0


@app.post("/api/v1/llm/generate")
async def llm_generate(
    request: GenerateRequest,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Generate a response from the NVIDIA model via Nebius Token Factory.

    This is a development/testing endpoint for LLM integration verification.
    It does not expose any API keys or provider-specific secrets.
    """
    from .llm.client import get_client, is_configured

    if not is_configured():
        return {
            "success": False,
            "model": request.model or "nebius/Nemotron-3_5-Lightning",
            "response": "",
            "error": "NEBIUS_API_KEY not configured. Set it in .env file.",
        }

    client = get_client()

    response = await client.generate(
        prompt=request.prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
        top_p=request.top_p,
    )

    return response.model_dump()


# --- Workspaces API ---------------------------------------------------------

_CLONE_ROOT = PROJECT_ROOT / "cloned_repos"
_GITHUB_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
_GITHUB_NAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98})$")


class CloneRepoRequest(BaseModel):
    owner: str
    name: str


def _register_workspace(ws_id: str, root: Path) -> dict:
    WORKSPACE_MAPPING[ws_id] = str(root)
    return {
        "id": ws_id,
        "name": root.name or ws_id,
        "path": str(root),
        "branch": _git_branch(root),
    }


@app.post("/api/v1/repos/clone")
async def clone_repo(
    request: CloneRepoRequest,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Shallow-clone a public GitHub repository into the managed clone root.

    The cloned directory is registered as a workspace so the file tree,
    file viewer, and agent can operate on it exactly like the built-in
    workspace roots. Owner/name are strictly validated — the clone URL is
    constructed server-side, never taken from the client (no SSRF).
    """
    owner = request.owner.strip()
    name = request.name.strip().removesuffix(".git")
    if not _GITHUB_OWNER_RE.fullmatch(owner) or not _GITHUB_NAME_RE.fullmatch(name):
        raise HTTPException(status_code=400, detail="Invalid repository owner or name")

    ws_id = f"gh-{owner}-{name}"
    dest = _CLONE_ROOT / f"{owner}__{name}"
    if ws_id in WORKSPACE_MAPPING and dest.is_dir():
        return _register_workspace(ws_id, dest)

    import shutil

    if dest.is_dir():
        if (dest / ".git").is_dir():
            # A clone from a previous process still exists on disk. Workspace
            # registration is in-memory and resets on restart — adopt it
            # instead of failing on a non-empty destination.
            return _register_workspace(ws_id, dest)
        shutil.rmtree(dest, ignore_errors=True)

    _CLONE_ROOT.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{owner}/{name}.git"
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="git clone timed out") from exc
    if result.returncode != 0:
        # Never echo the full git output — surface a short, safe reason.
        shutil.rmtree(dest, ignore_errors=True)
        stderr = (result.stderr or "").strip().splitlines()
        reason = stderr[-1] if stderr else f"git exited {result.returncode}"
        raise HTTPException(status_code=502, detail=f"Clone failed: {reason}")

    return _register_workspace(ws_id, dest)


@app.get("/api/v1/workspaces")
async def list_workspaces(
    user_uid: str = Depends(get_current_user),
) -> list[dict]:
    """List configured workspace roots with real git metadata."""
    out: list[dict] = []
    for ws_id, root in WORKSPACE_MAPPING.items():
        path = Path(root)
        out.append(
            {
                "id": ws_id,
                "name": path.name or ws_id,
                "path": str(path),
                "branch": _git_branch(path) if path.is_dir() else "",
            }
        )
    return out


@app.get("/api/v1/workspaces/{workspace_id}/tree")
async def workspace_tree(
    workspace_id: str,
    max_depth: int = Query(default=4, ge=1, le=8),
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Return the file tree of a workspace (skip dirs, bounded size)."""
    root = _resolve_workspace(workspace_id)
    if root is None:
        return _error_response(404, f"Unknown workspace: {workspace_id}")
    budget = [_TREE_NODE_BUDGET]
    return _build_tree(root, "", 0, max_depth, budget)


@app.get("/api/v1/workspaces/{workspace_id}/file")
async def workspace_file(
    workspace_id: str,
    path: str,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Read a single file from a workspace with path and sensitivity guards."""
    root = _resolve_workspace(workspace_id)
    if root is None:
        return _error_response(404, f"Unknown workspace: {workspace_id}")

    if not path or path.startswith(("/", "\\")) or ".." in path.split("/"):
        return _error_response(400, "Path must be a relative path inside the workspace")
    if _is_sensitive(path):
        return _error_response(403, "Access to this file is not allowed")

    target = (root / path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return _error_response(400, "Path must stay inside the workspace")

    if not target.is_file():
        return _error_response(404, f"File not found: {path}")

    try:
        raw = target.read_bytes()
    except OSError:
        return _error_response(404, f"File not readable: {path}")

    truncated = len(raw) > _FILE_MAX_BYTES
    if truncated:
        raw = raw[:_FILE_MAX_BYTES]
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("utf-8", errors="replace")

    return {
        "path": path,
        "content": content,
        "truncated": truncated,
        "bytes": len(raw),
    }


# --- Agent API --------------------------------------------------------------


class AgentRequest(BaseModel):
    workspace_id: str = "local-project"
    task: str
    max_iterations: int | None = None


@app.post("/api/v1/agent/analyze")
async def agent_analyze(
    request: AgentRequest,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Run the CodeForge AI coding agent on a task.

    The agent can inspect and modify files inside the configured workspace
    using its toolset (list/read/search, apply_patch/inspect_diff/write_file,
    run_tests). Returns a structured response including plan, observations
    and real run metrics (duration, tokens, model).
    """
    from .agent.agent import run_agent_task

    max_iterations = request.max_iterations or 10

    # Strict allow-list: the agent may only operate on configured workspaces —
    # never on an arbitrary path supplied by the client.
    workspace_root = WORKSPACE_MAPPING.get(request.workspace_id)

    if workspace_root is None or not os.path.isdir(workspace_root):
        detail = f"Unknown workspace: {request.workspace_id}"
        return {
            "success": False,
            "status": "error",
            "summary": detail,
            "files_inspected": [],
            "tools_used": [],
            "plan": [],
            "observations": [],
            "error": detail,
            "iteration": 0,
            "files_changed": [],
            "modification_count": 0,
            "diff_summary": "",
            "tokens_used": 0,
            "duration_seconds": 0.0,
            "model": "",
            "repair_attempts": 0,
            "max_repair_iterations": 5,
            "max_iterations": max_iterations,
            "phase": "",
        }

    response = await run_agent_task(
        workspace_root=workspace_root,
        task=request.task,
        max_iterations=max_iterations,
    )

    data = response.model_dump()
    data["max_iterations"] = max_iterations
    return data


# --- Runs API (persisted agent runs, Supabase-backed) ----------------------


class RunRequest(BaseModel):
    workspace_id: str = "local-project"
    task: str
    max_iterations: int | None = None


def _metrics_from(data: dict) -> dict:
    return {
        "tokensUsed": data.get("tokens_used", 0),
        "durationSeconds": data.get("duration_seconds", 0.0),
        "model": data.get("model", ""),
        "iterations": data.get("iteration", 0),
        "maxIterations": data.get("max_iterations", 10),
        "filesChanged": len(data.get("files_changed", [])),
        "repairAttempts": data.get("repair_attempts", 0),
        "toolsUsed": data.get("tools_used", []),
    }


@app.post("/api/v1/runs")
async def create_run(
    request: RunRequest,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Run the agent and persist the run (status, metrics, events) for `user_uid`.

    Fails closed with 503 when Supabase storage is not configured — a run is
    never executed without being recorded, and nothing is faked client-side.
    """
    from .agent.agent import run_agent_task

    max_iterations = request.max_iterations or 10
    # Strict allow-list — same rule as /agent/analyze: no arbitrary paths.
    workspace_root = WORKSPACE_MAPPING.get(request.workspace_id)
    if workspace_root is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workspace: {request.workspace_id}",
        )

    run_id = store.start_run(
        user_uid,
        task=request.task,
        workspace_id=request.workspace_id,
    )

    try:
        if not os.path.isdir(workspace_root):
            raise ValueError(f"Workspace root not found: {workspace_root}")

        response = await run_agent_task(
            workspace_root=workspace_root,
            task=request.task,
            max_iterations=max_iterations,
        )
        data = response.model_dump()
        data["max_iterations"] = max_iterations

        store.finish_run(
            run_id,
            user_uid,
            status="COMPLETED" if data.get("success") else "FAILED",
            summary=data.get("summary", ""),
            error=data.get("error"),
            metrics=_metrics_from(data),
            plan=data.get("plan", []),
            files_inspected=data.get("files_inspected", []),
            files_changed=data.get("files_changed", []),
            diff_summary=data.get("diff_summary", ""),
            observations=data.get("observations", []),
            events=data.get("events", []),
        )
        return {"run_id": run_id, **data}
    except Exception as exc:  # noqa: BLE001 — record the failure, then re-raise
        try:
            store.finish_run(
                run_id,
                user_uid,
                status="FAILED",
                summary="",
                error=str(exc),
                metrics={
                    "tokensUsed": 0,
                    "durationSeconds": 0.0,
                    "model": "",
                    "iterations": 0,
                    "maxIterations": max_iterations,
                    "filesChanged": 0,
                    "repairAttempts": 0,
                    "toolsUsed": [],
                },
                plan=[],
                files_inspected=[],
                files_changed=[],
                diff_summary="",
                observations=[],
                events=[],
            )
        except Exception:  # noqa: BLE001 — persistence already unavailable
            pass
        raise


@app.get("/api/v1/runs")
async def list_runs(
    limit: int = Query(default=10, ge=1, le=50),
    cursor: Optional[float] = Query(default=None),
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Newest-first page of the caller's own runs."""
    return store.list_runs(user_uid, limit=limit, cursor=cursor)


@app.get("/api/v1/runs/{run_id}")
async def get_run(
    run_id: str,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Fetch one run. 404 unknown, 403 when it belongs to another user."""
    return store.get_run(user_uid, run_id)


@app.get("/api/v1/runs/{run_id}/events")
async def get_run_events(
    run_id: str,
    limit: int = Query(default=25, ge=1, le=50),
    cursor: Optional[float] = Query(default=None),
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Paginated event timeline of one of the caller's runs."""
    return store.list_run_events(user_uid, run_id, limit=limit, cursor=cursor)
