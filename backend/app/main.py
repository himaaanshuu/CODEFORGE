"""CodeForge AI FastAPI backend.

Public routes (`/`, `/health`) stay open. API routes under `/api/v1` are
protected by Supabase access-token verification (see `backend/auth_dep.py`).
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load backend/.env before any module reads environment configuration.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr

from backend import supabase_service as store
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
# The application source is never exposed as a user workspace. Clones are
# stored and registered per authenticated user.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

WORKSPACE_MAPPING: dict[str, str] = {}
WORKSPACE_OWNERS: dict[str, str] = {}

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


def _user_workspace_key(user_uid: str) -> str:
    """Return a stable, non-reversible filesystem namespace for one user."""
    import hashlib

    return hashlib.sha256(user_uid.encode("utf-8")).hexdigest()[:24]


def _adopt_existing_clones(user_uid: str) -> None:
    """Re-register only the authenticated user's clones after a restart."""
    user_root = _CLONE_ROOT / _user_workspace_key(user_uid)
    try:
        entries = list(user_root.iterdir())
    except OSError:
        return
    for entry in entries:
        if not entry.is_dir() or "__" not in entry.name:
            continue
        owner, _, name = entry.name.partition("__")
        if not owner or not name:
            continue
        if not _GITHUB_OWNER_RE.fullmatch(owner) or not _GITHUB_NAME_RE.fullmatch(name):
            continue
        if not (entry / ".git").is_dir():
            continue
        ws_id = f"gh-{_user_workspace_key(user_uid)}-{owner}-{name}"
        WORKSPACE_MAPPING[ws_id] = str(entry)
        WORKSPACE_OWNERS[ws_id] = user_uid


def _resolve_workspace(workspace_id: str, user_uid: str) -> Path | None:
    if WORKSPACE_OWNERS.get(workspace_id) != user_uid:
        _adopt_existing_clones(user_uid)
    if WORKSPACE_OWNERS.get(workspace_id) != user_uid:
        return None
    root = WORKSPACE_MAPPING.get(workspace_id)
    if root is not None:
        path = Path(root)
        if path.is_dir():
            return path
        WORKSPACE_MAPPING.pop(workspace_id, None)
        WORKSPACE_OWNERS.pop(workspace_id, None)
    return None


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


class PublishChangesRequest(BaseModel):
    files: list[str] = Field(min_length=1, max_length=100)
    branch_name: str = Field(min_length=1, max_length=55, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    commit_message: str = Field(min_length=1, max_length=120)
    github_token: SecretStr


def _validated_workspace_paths(root: Path, paths: list[str]) -> list[str]:
    validated: list[str] = []
    for raw_path in dict.fromkeys(paths):
        path = Path(raw_path)
        if (
            not raw_path
            or raw_path.startswith(":")
            or "\\" in raw_path
            or path.is_absolute()
            or ".." in path.parts
        ):
            raise HTTPException(status_code=400, detail="Invalid changed-file path")
        resolved = (root / path).resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Changed file is outside the workspace") from exc
        validated.append(path.as_posix())
    if not validated:
        raise HTTPException(status_code=400, detail="No changed files were selected")
    return validated


def _run_git(root: Path, *args: str, timeout: int = 30, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
            timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Git operation timed out") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail="Git is not installed on the backend") from exc


def _askpass_files(directory: Path) -> tuple[Path, Path]:
    """Create short-lived askpass scripts; the GitHub token stays in process env."""
    python_script = directory / "askpass.py"
    python_script.write_text(
        "import sys\n"
        "prompt = sys.argv[1].lower() if len(sys.argv) > 1 else ''\n"
        "print('x-access-token' if 'username' in prompt else __import__('os').environ['CODEFORGE_GITHUB_TOKEN'])\n",
        encoding="utf-8",
    )
    if os.name == "nt":
        command_script = directory / "askpass.cmd"
        command_script.write_text(
            f'@"{sys.executable}" "{python_script}" "%~1"\r\n',
            encoding="utf-8",
        )
    else:
        command_script = directory / "askpass"
        command_script.write_text(
            f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(python_script))} \"$1\"\n",
            encoding="utf-8",
        )
        command_script.chmod(0o700)
    return command_script, python_script


def _register_workspace(ws_id: str, root: Path, user_uid: str) -> dict:
    WORKSPACE_MAPPING[ws_id] = str(root)
    WORKSPACE_OWNERS[ws_id] = user_uid
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

    user_key = _user_workspace_key(user_uid)
    ws_id = f"gh-{user_key}-{owner}-{name}"
    user_root = _CLONE_ROOT / user_key
    dest = user_root / f"{owner}__{name}"
    if ws_id in WORKSPACE_MAPPING and dest.is_dir():
        return _register_workspace(ws_id, dest, user_uid)

    import shutil

    if dest.is_dir():
        if (dest / ".git").is_dir():
            # A clone from a previous process still exists in this user's
            # directory. Adopt it instead of failing on a non-empty destination.
            return _register_workspace(ws_id, dest, user_uid)
        shutil.rmtree(dest, ignore_errors=True)

    user_root.mkdir(parents=True, exist_ok=True)
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

    return _register_workspace(ws_id, dest, user_uid)


@app.post("/api/v1/workspaces/{workspace_id}/git/publish")
async def publish_workspace_changes(
    workspace_id: str,
    request: PublishChangesRequest,
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Commit selected agent changes on a new branch and push it to GitHub."""
    root = _resolve_workspace(workspace_id, user_uid)
    if root is None:
        raise HTTPException(status_code=404, detail="Unknown workspace")
    root = Path(root).resolve()

    top = _run_git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise HTTPException(status_code=400, detail="Workspace root is not a Git repository")

    remote = _run_git(root, "remote", "get-url", "origin")
    if remote.returncode != 0:
        raise HTTPException(status_code=400, detail="Workspace has no GitHub origin remote")
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:)([A-Za-z0-9](?:[A-Za-z0-9-]{0,38})?)/([A-Za-z0-9](?:[A-Za-z0-9._-]{0,98})?)(?:\.git)?/?",
        remote.stdout.strip(),
        flags=re.IGNORECASE,
    )
    if not match:
        raise HTTPException(status_code=400, detail="Origin must be a GitHub repository")
    owner, repo = match.groups()
    repo = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)

    branch = f"codeforge/{request.branch_name}"
    if ".." in branch or branch.endswith((".", ".lock", "/")):
        raise HTTPException(status_code=400, detail="Invalid branch name")

    files = _validated_workspace_paths(root, request.files)
    blocked_suffixes = {".pem", ".key", ".p12", ".pfx"}
    for raw_path in files:
        path = Path(raw_path)
        basename = path.name.lower()
        if (basename == ".env" or basename.startswith(".env.")) and basename not in {
            ".env.example", ".env.sample"
        }:
            raise HTTPException(status_code=400, detail="Secret environment files cannot be pushed")
        if path.suffix.lower() in blocked_suffixes:
            raise HTTPException(status_code=400, detail="Private key and certificate files cannot be pushed")

    staged = _run_git(root, "diff", "--cached", "--quiet")
    if staged.returncode == 1:
        raise HTTPException(status_code=409, detail="Commit or unstage existing staged changes first")
    if staged.returncode != 0:
        raise HTTPException(status_code=400, detail="Could not inspect staged Git changes")

    token = request.github_token.get_secret_value()
    import httpx

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            user_response = await client.get("https://api.github.com/user", headers=headers)
            if user_response.status_code != 200:
                raise HTTPException(status_code=401, detail="GitHub authorization expired; reconnect GitHub")
            github_user = user_response.json()
            repo_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}", headers=headers
            )
            if repo_response.status_code != 200:
                raise HTTPException(status_code=403, detail="GitHub token cannot access this repository")
            permissions = repo_response.json().get("permissions") or {}
            if permissions.get("push") is not True:
                raise HTTPException(
                    status_code=403,
                    detail="GitHub authorization needs write access to this repository; reconnect with repository access",
                )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Timed out checking GitHub authorization") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not reach GitHub to verify repository access") from exc

    existing_branch = _run_git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}")
    if existing_branch.returncode == 0:
        raise HTTPException(status_code=409, detail=f"Branch {branch} already exists in this workspace")

    switch = _run_git(root, "switch", "-c", branch)
    if switch.returncode != 0:
        raise HTTPException(status_code=400, detail=f"Could not create branch: {switch.stderr.strip()[:300]}")

    add = _run_git(root, "add", "--", *files)
    if add.returncode != 0:
        raise HTTPException(status_code=400, detail=f"Could not stage selected files: {add.stderr.strip()[:300]}")
    staged_diff = _run_git(root, "diff", "--cached", "--quiet")
    if staged_diff.returncode == 0:
        raise HTTPException(status_code=400, detail="Selected files have no uncommitted changes")
    if staged_diff.returncode != 1:
        raise HTTPException(status_code=400, detail="Could not inspect selected changes")

    login = str(github_user.get("login") or "CodeForge User")
    github_id = str(github_user.get("id") or "")
    _run_git(root, "config", "user.name", login)
    _run_git(root, "config", "user.email", f"{github_id}+{login}@users.noreply.github.com")
    commit = _run_git(root, "commit", "-m", request.commit_message.strip(), timeout=60)
    if commit.returncode != 0:
        raise HTTPException(status_code=400, detail=f"Commit failed: {commit.stderr.strip()[:500]}")
    sha_result = _run_git(root, "rev-parse", "HEAD")
    commit_sha = sha_result.stdout.strip()[:12]

    with tempfile.TemporaryDirectory(prefix="codeforge-askpass-") as temp_dir:
        askpass, _ = _askpass_files(Path(temp_dir))
        env = os.environ.copy()
        env.update(
            {
                "CODEFORGE_GITHUB_TOKEN": token,
                "GIT_ASKPASS": str(askpass),
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        push = _run_git(
            root,
            "-c", "credential.helper=",
            "-c", f"core.askPass={askpass}",
            "-c", f"remote.origin.pushurl=https://github.com/{owner}/{repo}.git",
            "push", "--set-upstream", "origin", branch,
            timeout=90,
            env=env,
        )
    if push.returncode != 0:
        detail = (push.stderr or "GitHub rejected the push").strip()[-500:]
        raise HTTPException(
            status_code=502,
            detail=f"Commit {commit_sha} is saved locally on {branch}, but push failed: {detail}",
        )

    return {
        "branch": branch,
        "commit": commit_sha,
        "repository": f"{owner}/{repo}",
        "url": f"https://github.com/{owner}/{repo}/tree/{branch}",
        "message": "Changes committed and pushed to GitHub.",
    }


@app.get("/api/v1/workspaces/{workspace_id}/git/diff")
async def workspace_git_diff(
    workspace_id: str,
    files: list[str] = Query(min_length=1, max_length=100),
    user_uid: str = Depends(get_current_user),
) -> dict:
    """Return a bounded working-tree diff for selected workspace files."""
    root = _resolve_workspace(workspace_id, user_uid)
    if root is None:
        raise HTTPException(status_code=404, detail="Unknown workspace")
    root = Path(root).resolve()
    top = _run_git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root:
        raise HTTPException(status_code=400, detail="Workspace root is not a Git repository")
    validated = _validated_workspace_paths(root, files)
    result = _run_git(root, "diff", "--no-ext-diff", "--unified=3", "HEAD", "--", *validated)
    if result.returncode != 0:
        raise HTTPException(status_code=400, detail="Could not read workspace diff")
    return {"diff": result.stdout[:200_000], "truncated": len(result.stdout) > 200_000}


@app.get("/api/v1/workspaces")
async def list_workspaces(
    user_uid: str = Depends(get_current_user),
) -> list[dict]:
    """List configured workspace roots with real git metadata."""
    # Re-adopt on-disk clones so the picker repopulates after a restart.
    _adopt_existing_clones(user_uid)
    out: list[dict] = []
    for ws_id, root in WORKSPACE_MAPPING.items():
        if WORKSPACE_OWNERS.get(ws_id) != user_uid:
            continue
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
    root = _resolve_workspace(workspace_id, user_uid)
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
    root = _resolve_workspace(workspace_id, user_uid)
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
    workspace_id: str
    task: str
    max_iterations: int | None = None
    model: str | None = None


def _agent_error_envelope(detail: str, max_iterations: int) -> dict:
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
    from .llm.models import resolve_model

    max_iterations = request.max_iterations or 10

    # Strict allow-list on the model as well: unknown IDs/labels are rejected
    # before any work happens, so a bad value can never silently run on Ultra.
    try:
        model_name = resolve_model(request.model)
    except ValueError as exc:
        return _agent_error_envelope(str(exc), max_iterations)

    # Strict allow-list: the agent may only operate on configured workspaces —
    # never on an arbitrary path supplied by the client. _resolve_workspace
    # also re-adopts on-disk clones lost by a backend restart.
    resolved = _resolve_workspace(request.workspace_id, user_uid)

    if resolved is None:
        detail = f"Unknown workspace: {request.workspace_id}"
        return _agent_error_envelope(detail, max_iterations)

    response = await run_agent_task(
        workspace_root=str(resolved),
        task=request.task,
        max_iterations=max_iterations,
        model=model_name,
    )

    data = response.model_dump()
    data["max_iterations"] = max_iterations
    return data


# --- Runs API (persisted agent runs, Supabase-backed) ----------------------


class RunRequest(BaseModel):
    workspace_id: str
    task: str
    max_iterations: int | None = None
    model: str | None = None


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
    from .llm.models import resolve_model

    max_iterations = request.max_iterations or 10
    try:
        model_name = resolve_model(request.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    # Strict allow-list — same rule as /agent/analyze: no arbitrary paths.
    # _resolve_workspace also re-adopts on-disk clones lost by a restart.
    resolved = _resolve_workspace(request.workspace_id, user_uid)
    if resolved is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown workspace: {request.workspace_id}",
        )
    workspace_root = str(resolved)

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
            model=model_name,
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
