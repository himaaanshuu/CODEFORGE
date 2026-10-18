# Architecture — CodeForge AI

> System design: components, data flows, agent loop, and deployment topology.
> See [context.md](context.md) · [requirements.md](requirements.md) · [design.md](design.md).

## 1. System Overview

```text
┌───────────────────────────┐        HTTPS/JSON         ┌────────────────────────────┐
│  Frontend (Vercel)        │ ────────────────────────▶ │  Backend (Render, FastAPI) │
│  React 19 + Vite + TS     │   Bearer: Supabase JWT    │  uvicorn, ASGI             │
│  codeforge-delta-ivory…   │ ◀──────────────────────── │  codeforge-ke01.onrender…  │
└────────────┬──────────────┘                           └──────┬───────────┬─────────┘
             │ Supabase JS (auth + anon reads)                 │           │
             ▼                                                 ▼           ▼
┌───────────────────────────┐                     ┌───────────────┐  ┌──────────────┐
│  Supabase                 │ ◀── PostgREST ───── │ Workspace FS  │  │ Nebius LLM   │
│  Auth (GitHub OAuth)      │     service role    │ cloned_repos/ │  │ Token Factory│
│  Postgres (RLS deny-all)  │                     │ chroot-bound  │  │ Nemotron-3   │
└───────────────────────────┘                     └───────────────┘  └──────────────┘
```

Trust boundaries:

1. **Browser** — untrusted; only holds anon key + its own JWT.
2. **Backend** — sole privileged actor: service-role DB access, filesystem inside workspace roots, LLM API key.
3. **Sandbox** — `run_tests` subprocesses: allow-listed commands, sanitized env, timeout/output caps.

## 2. Backend Layout

```text
backend/
├── app/
│   ├── main.py            # FastAPI app, CORS, all HTTP endpoints
│   ├── config.py          # env loader
│   ├── auth_middleware.py # fail-closed JWT middleware (401/503)
│   ├── agent/
│   │   ├── agent.py       # run_agent_task loop, batching, repeat guard, repair
│   │   ├── models.py      # events, states, request schemas
│   │   ├── prompts.py     # system prompt + response contract
│   │   └── state.py       # iteration/repair tracker (set_plan, etc.)
│   ├── tools/
│   │   ├── base.py        # ToolBase contract, ToolResult
│   │   ├── registry.py    # register / get / list_tools / execute_tool
│   │   ├── repository_tools.py   # list_files, read_file, search_code
│   │   ├── modification_tools.py # apply_patch, inspect_diff, write_file
│   │   └── execution_tools.py    # run_tests
│   ├── execution/
│   │   ├── runner.py      # sandboxed subprocess runner (60s, SIGALRM, 100KB)
│   │   └── models.py
│   ├── llm/
│   │   ├── client.py      # OpenAI-compatible client → Nebius
│   │   └── models.py
│   └── repository/
│       └── workspace.py   # Workspace.resolve() + boundary checks
├── supabase_auth.py       # HS256 + JWKS token verification
├── supabase_service.py    # PostgREST client: runs, events, usage
├── auth_dep.py            # DI dependency
└── tests/                 # 113 pytest tests
```

### API surface

| Method & path | Purpose |
|---|---|
| `GET /` · `GET /health` | Info / liveness |
| `POST /api/v1/llm/generate` | Raw LLM completion (Prompt Lab, ad-hoc) |
| `POST /api/v1/repos/clone` | Shallow clone `{owner, name}` → workspace |
| `GET /api/v1/workspaces` | List workspaces |
| `GET /api/v1/workspaces/{id}/tree` | Directory tree |
| `GET /api/v1/workspaces/{id}/file` | File content (path-validated) |
| `POST /api/v1/agent/analyze` | Stateless agent run |
| `POST /api/v1/runs` | Persistent agent run |
| `GET /api/v1/runs` · `/runs/{id}` · `/runs/{id}/events` | History |

All `/api/v1/*` routes sit behind the fail-closed auth middleware.

## 3. Workspace Model

- Workspace id: `gh-{owner}-{name}`. Clone dir: `cloned_repos/{owner}__{name}`.
- `WORKSPACE_MAPPING` is an in-memory id→dir map, **self-healing**:
  - `_adopt_existing_clones()` scans `cloned_repos/` on startup and re-registers git checkouts (Render free tier restarts with ephemeral memory, persistent-ish disk between deploys).
  - `_resolve_workspace()` falls back to re-adoption when an id is missing; rejects traversal ids.
- Every tool resolves paths through `Workspace.resolve()`, which requires the target to exist and remain inside the root; new files go through `_validate_new_path`.
- `/agent/analyze`, `POST /runs`, and the workspace list endpoints all route through the resolver — a single choke point for boundary enforcement.

## 4. Agent Loop (`run_agent_task`)

```text
         ┌──────────────────────────────────────────────┐
         ▼                                              │
  build system prompt + tool schemas + history          │
         │                                              │
         ▼                                              │
  LLM call (temperature 0.3, max_tokens 2000)           │
         │                                              │
         ▼                                              │
  _parse_llm_response                                   │
    ├─ final_analysis ──▶ persist plan, emit result ────┤ (stop)
    ├─ tool_call (single JSON)                          │
    └─ tool_calls  (batch: one JSON object per line)    │
         │                                              │
         ▼                                              │
  for each call: _run_single_tool                       │
    ├─ repeat guard (identical call ×2 → corrective     │
    │   observation; ×3 → force final)                  │
    ├─ registry.execute_tool(...)                       │
    ├─ record events / repair counter / tool counts     │
    └─ failures feed failure_history                    │
         │                                              │
         ▼                                              │
  test results? ── fail & budget left ──▶ REPAIRING ────┘
                    (failure history injected)
```

Key mechanisms:

- **Batched tool calls.** The Nemotron endpoint emits one JSON object per line; `_extract_all_json_objects` (+nested-object filtering and dedupe) collects them; `final` inside a batch takes precedence over further tool work. This raised per-iteration throughput ~5× (≈11 executions in 4 iterations vs 2+ iterations per call previously).
- **Repeat guard.** `last_call_key` / `consecutive_repeats`; `run_tests` exempt so re-verification still works.
- **Repair loop.** Max 5 attempts; each failing `run_tests` increments the counter and appends to failure history carried in the next prompt.
- **Plan persistence.** `state.set_plan` on final answer; synthesized on the tests-passed path; never wiped by response initialization.
- **Events.** Structured payloads (`tool_name`, `observation`, top-level fields merged into DB `data`) drive the UI timeline and history API.

## 5. Notable Tool Implementations

### `apply_patch` (unified diff)

1. Split input into per-file diffs; detect new files via `/dev/null` (validated with `_validate_new_path`).
2. Parse hunks; apply sequentially with running offsets; per-hunk search = offset ±5 then full-file rescan.
3. Context matching is whitespace-tolerant but writes **original** context indentation.
4. **Atomic per file:** build the new content first; write only on full success — a failed patch leaves bytes unchanged.

### `inspect_diff`

Runs real `git diff` / `git status` / `git diff --numstat` inside the workspace; output capped ~12k chars; non-git workspaces get an honest "not a git repository" message instead of fake data.

### `run_tests`

Allow-list filter (pytest/npm test/etc. only), sanitized environment, 60s wall timeout via SIGALRM, 100KB stdout/stderr cap, structured `TestRun` result.

## 6. Auth & Data Flow

1. Browser → Supabase OAuth (GitHub) → JWT in session.
2. Browser calls backend with `Authorization: Bearer <jwt>`.
3. Middleware verifies: HS256 via `SUPABASE_JWT_SECRET`, exp check, RS256/JWKS fallback. Any failure → 401; missing config → 503.
4. Persisted writes (runs, events, usage) use the service-role PostgREST client — RLS denies all direct client access, so the backend is the only privileged path.
5. Event rows store merged top-level fields in `data` so history replay matches live events.

## 7. Frontend Layout

```text
frontend/src/
├── App.tsx                  # routing between Landing / Auth / Workspace views
├── screens/                 # Landing, Auth (login), GithubConnect, Workspace
├── components/
│   ├── layout/              # Header, Sidebar
│   ├── agent/               # status pill, PromptComposer, timeline, AgentStatus
│   ├── run/                 # ChangesTab, TestsTab, VerificationTab
│   ├── code/                # DiffViewer
│   ├── repository/          # repo pickers, tree
│   ├── insights/            # usage, efficiency, architecture map
│   └── ui/                  # Button, Alert, Tabs, ThemeToggle, GithubMark…
├── hooks/                   # useAgentRun (AgentController), useTheme
├── lib/                     # supabase client, promptScore, agentState, format
└── types/                   # shared TS models (AgentState, FileChange, …)
```

Workspace renders by `view` state: repositories · files · agent · changes · tests · architecture · prompt · usage · efficiency. The agent view consumes an `AgentController` hook that POSTs `/runs`, streams events into local state, and exposes `state`, `events`, `run`, `reset()`.

## 8. Deployment Topology

| Piece | Host | Notes |
|---|---|---|
| SPA | Vercel (`codeforge-delta-ivory.vercel.app`) | `vercel.json` SPA rewrite; `VITE_*` as **Config** vars (build-time baking) |
| API | Render (`codeforge-ke01.onrender.com`) | Free tier; sleeps when idle; ephemeral disk; `FRONTEND_ORIGINS` lists every frontend origin |
| Auth/DB | Supabase | GitHub provider; redirect URLs must include every frontend origin |

Operational consequences handled in code: cold-start latency (acceptable), disk wipe → re-clone, restart → workspace re-adoption (§3).

## 9. Testing Architecture

- **Backend (`backend/tests`, 113 tests):** auth (JWT/middleware/CORS), workspace security (traversal), API endpoints, agent loop (events, failure recovery, batching, repeat guard), LLM client, Supabase service, patch tools (multi-file, new-file, atomic failure, whitespace tolerance).
- `conftest.py` disables the auth middleware autouse so tests call routes directly with `backend.app.*` imports.
- **Frontend:** `tsc -b` (strict), `oxlint`, production build as the gate; E2E scripts live outside the repo (temp dir) for live clone/repair scenarios.

## 10. Design Constraints & Trade-offs

- **Single-agent, single-loop** (no multi-agent orchestration): simpler failure surface, adequate for repo-edit tasks; roadmap may add planner/executor splits later.
- **In-memory workspace map + disk adoption** instead of DB-persisted paths: survives restarts without schema coupling; trade-off is the scan-on-adopt heuristic.
- **Tool-call JSON-in-text protocol** rather than native function calling: required by the Nemotron endpoint's emission format; parser is defensive (per-line objects, nested filtering).
- **Free-tier hosting**: Render sleep + ephemeral disk accepted for cost; mitigated by self-healing workspaces and lazy cloning.
