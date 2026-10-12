# CodeForge AI
# Autonomous AI software engineering agent for Nebius × NVIDIA Global AI Hackathon 2026

# 🎯 Project Status: Phases 4-6 Complete

**CodeForge AI** is now operational across all three development stages:

- ✅ **Phase 4**: Safe code modification (apply_patch, inspect_diff tools)
- ✅ **Phase 5**: Sandboxed test execution (execution policy, runner, run_tests tool)
- ✅ **Phase 6**: Autonomous failure recovery (repair loop, failure analysis, stop conditions)

**Both servers running**:
- Backend (FastAPI): http://localhost:8000
- Frontend (React+Vite): http://localhost:5173
- **25/25 backend tests passing**

---

# 🚀 Overview

CodeForge AI is an **autonomous coding agent** that can:

1. **Understand** a coding task
2. **Explore** a repository using `list_files`, `search_code`, `read_file`
3. **Plan** an implementation approach
4. **Modify** code using controlled `apply_patch` (unified diff patches)
5. **Inspect** the resulting diff
6. **Run tests** in a sandboxed environment (`run_tests` tool)
7. **Diagnose** test failures
8. **Repair** code through iterative patches (max 5 repair attempts)
9. **Verify** fixes pass the full test suite

The system is **workspace-scoped and sandbox-oriented** — no unrestricted shell access, no arbitrary command execution, no network access from test processes.

---

# 🏗️ Architecture

```text
USER TASK
    ↓
UNDERSTAND   (list_files, search_code, read_file)
    ↓
PLAN         (agent reasoning)
    ↓
MODIFY      (apply_patch — unified diff patches)
    ↓
INSPECT DIFF (inspect_diff)
    ↓
RUN TESTS   (run_tests — sandboxed)
    │
   ┌───────────────┐
   │               │
  PASS            FAIL
    │               │
    ▼               ▼
VERIFY      DIAGNOSE
    │               │
    │             FIX
    │               │
    │             TEST AGAIN
    │               │
    │          ┌────┴────┐
    │          │         │
    │         PASS      FAIL
    │          │         │
    └──────────┴─────────┘
              ↓
        FINAL RESULT (structured evidence)
```

---

# 🛠️ Features

## Phase 4 — Safe Code Modification

- **`apply_patch`**: Apply unified diff patches with full path validation
  - Rejects absolute paths, `../` traversal, paths outside workspace
  - Rejects `.git` directory, system paths, forbidden files
  - Atomic: validates, applies, or reports errors completely
- **`inspect_diff`**: Inspect current workspace changes
  - Returns files changed, insertions, deletions, diff summary
- **`write_file`**: Restricted file writing (workspace-only)
- Agent no longer READ-ONLY — can make controlled modifications
- Preferred sequence: `list_files → search_code → read_file → reason → plan → apply_patch → inspect_diff`

## Phase 5 — Sandboxed Test Execution

- **`run_tests` tool**: Run repository tests in controlled environment
  - Only allowed commands: `pytest`, `python`, `python3`
  - Forbidden: `rm`, `sudo`, `curl`, `wget`, `ssh`, `scp`, `kill`, `killall`
  - Timeout: 60 seconds (enforced via SIGALRM)
  - Output limits: 100KB stdout, 10KB stderr
  - Environment sanitization (removes secret/key/API variables)
  - Automatic pytest output parsing (passed/failed/skipped/errors counts)
- No network access during test execution
- Clean process cleanup

## Phase 6 — Autonomous Failure Recovery

- **Repair loop**: Maximum 5 repair attempts per task
- **Failure history**: Stores last 10 failures with modifications and summaries
- **Phase tracking**: `exploration → planning → modification → testing → failure_analysis → repair → verification → completed/failed`
- **Automatic failure detection**: Triggers when tests fail
- **Failure analysis**: LLM analyzes failures and generates targeted patches
- **Regression protection**: Full test suite must pass before success declaration
- **Stop conditions**:
  - **SUCCESS**: Target issue fixed, relevant tests pass, full suite passes
  - **FAILURE**: Max repair iterations reached, repeated identical failure, execution environment failure

---

# ⚡ Quick Start

```bash
# 1. Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Configure API key
cp backend/.env.example backend/.env
# Edit backend/.env and add your NEBIUS_API_KEY
# Add SUPABASE_* values (see 🔐 Supabase Setup) to enable sign-in
# Never commit .env files - they're gitignored

# 4. Run the backend
uvicorn backend.app.main:app --reload
# Server: http://localhost:8000

# 5. Run the frontend
cd frontend
cp .env.local.example .env.local   # fill in VITE_SUPABASE_* values
npm install
npm run dev
# Server: http://localhost:5173
```

---

# 📦 Available API Endpoints

All `/api/v1/*` routes require a Supabase access token (`Authorization: Bearer <token>`):

| Endpoint | Description |
|----------|-------------|
| `GET /` | "CodeForge AI is running" (public) |
| `GET /health` | "healthy" — service health check (public) |
| `POST /api/v1/llm/generate` | Generate response from NVIDIA model via Nebius |
| `POST /api/v1/agent/analyze` | Run the coding agent on a task (ephemeral) |
| `GET /api/v1/workspaces` | List workspaces with real git branch |
| `GET /api/v1/workspaces/{id}/tree` | Directory tree (sensitive dirs skipped) |
| `GET /api/v1/workspaces/{id}/file` | File contents (traversal/sensitive guarded) |
| `POST /api/v1/runs` | Run the agent **and persist** the run (status, metrics, events) |
| `GET /api/v1/runs` | Caller's own runs, newest first (cursor pagination) |
| `GET /api/v1/runs/{run_id}` | One run — 404 unknown, 403 another user's run |
| `GET /api/v1/runs/{run_id}/events` | Paginated event timeline of one run |

Auth failures fail closed: missing/malformed token → `401`; Supabase not
configured on the server → `503` with an explicit configuration error
(never a silent bypass).

---

# 📁 Project Structure

```
codeforge-ai/
├── backend/          # FastAPI backend (Python)
│   ├── app/          # Core application code
│   │   ├── agent/    # Agent orchestration loop
│   │   ├── llm/      # Nebius Token Factory client
│   │   ├── tools/    # Repository tools (list_files, read_file, search_code)
│   │   ├── modification_tools.py  # apply_patch, inspect_diff, write_file
│   │   ├── execution_tools.py     # run_tests tool
│   │   ├── execution/           # Execution models, policy, runner
│   │   └── repository/            # Workspace abstraction (path safety)
│   ├── tests/        # 25 unit tests (all passing)
│   └── requirements.txt
├── frontend/         # React + Vite frontend
│   ├── src/          # Source code
│   ├── package.json
│   ├── tailwind.config.cjs
│   └── vite.config.ts
├── tests/            # Fixture repositories for testing
└── README.md
```

---

# 🤖 NVIDIA + Nebius Integration

CodeForge AI uses **Nebius Token Factory** to access **NVIDIA open-source models**:

- **Model**: `nvidia/nemotron-3-ultra-550b-a55b` (configured in `NEBIUS_MODEL`)
- **Platform**: Nebius Token Factory (OpenAI-compatible interface at `https://api.tokenfactory.nebius.com/v1`)
- **API Key**: stored in `backend/.env`, never committed to repository
- The model runs on Nebius infrastructure, not locally

---

# 📦 Development Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your NEBIUS_API_KEY

# 4. Install and run frontend
cd frontend
npm install
npm run dev

# 5. Start both servers
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

# 📚 Environment Variables

**Backend (`backend/.env`)**

| Variable | Default | Description |
|----------|---------|-------------|
| `NEBIUS_API_KEY` | _(required)_ | Your Nebius API key |
| `NEBIUS_BASE_URL` | `https://api.tokenfactory.nebius.com/v1` | API base URL |
| `NEBIUS_MODEL` | `nvidia/Nemotron-3-Ultra-550b-a55b` | Model name (case-sensitive) |
| `DEBUG` | `False` | Debug mode |
| `SUPABASE_URL` | _(required)_ | Supabase project URL (`https://<ref>.supabase.co`) |
| `SUPABASE_JWT_SECRET` | _(required)_ | Auth JWT secret (HS256 token verification) |
| `SUPABASE_SERVICE_ROLE_KEY` | _(required)_ | Server-only service-role key (PostgREST writes) |
| `FRONTEND_ORIGINS` | `http://localhost:5173,...` | CORS allowed origins (comma-separated) |

**Frontend (`frontend/.env.local`)**

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE` | Backend base URL (default `http://localhost:8000/api`) |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` | Supabase project URL + anon (public) key |

`.env`, `frontend/.env.local` and `*.local` are gitignored — never commit secrets.

---

# 🔐 Supabase Setup (required to sign in)

Supabase Auth is the identity authority (GitHub-only sign-in); Supabase
Postgres persists runs. Until both halves below are configured the app
**fails closed**: the backend answers `503` on protected routes and the
frontend shows a configuration error on the sign-in screen (no mock users,
no bypass).

1. **Create the project** → https://supabase.com → *New project*.
2. **Enable GitHub sign-in**: *Authentication → Sign In → GitHub → Enable*
   → paste your GitHub OAuth App's Client ID + Client Secret
   (GitHub → Settings → Developer settings → OAuth Apps). Set the OAuth
   App's callback URL to the one Supabase shows:
   `https://<ref>.supabase.co/auth/v1/callback`.
3. **Run the schema**: *SQL Editor → New query* → paste
   `supabase/migrations/0001_init.sql` → **Run**. RLS is enabled with **no
   policies** — clients are denied all direct database access; only the
   backend's service-role key can read/write (server-owned persistence:
   clients can never forge runs, events, or usage records).
4. **Keys** → *Project Settings → API*:
   - `frontend/.env.local`: `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`
     (anon key is public by design).
   - `backend/.env`: `SUPABASE_URL` + `SUPABASE_JWT_SECRET` +
     `SUPABASE_SERVICE_ROLE_KEY` (service-role key is a **server secret** —
     never expose it to the browser or commit it).

---

# 🧪 Backend Tests

All **76 tests** pass (JWT verification runs for real with a test-owned
secret; PostgREST storage is faked in tests only):

| Test Suite | Tests | Purpose |
|------------|-------|---------|
| `test_agent.py` | 9 | Agent models, parsing, events |
| `test_api.py` | 12 | Workspace/file/tree endpoints (auth mocked) |
| `test_auth.py` | 14 | Real JWT verification: 401/503/sub wiring |
| `test_auth_middleware.py` | 9 | Pre-routing 401 + CORS headers/preflight |
| `test_supabase.py` | 16 | Run persistence, ownership isolation, RLS SQL |
| `test_llm.py` | 4 | LLM configuration/client (env-isolated) |
| `test_workspace_security.py` | 12 | Path traversal prevention |

Run: `cd backend && source .venv/bin/activate && python -m pytest --tb=short`

---

# 📜 License

**MIT** — Copyright (c) 2026 CodeForge AI. Open for hackathon public accessibility.

---

# 📬 Hackathon

**Nebius × NVIDIA Global AI Hackathon 2026**

Built with NVIDIA Nemotron models through Nebius Token Factory.