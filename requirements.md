# Requirements — CodeForge AI

> Functional and non-functional requirements for the CodeForge AI platform.
> Status legend: ✅ implemented · 🔄 in development · 🔜 planned.
> See [context.md](context.md) · [architecture.md](architecture.md) · [design.md](design.md).

## 1. Functional Requirements

### FR-1 — Authentication & Identity

| ID | Requirement | Status |
|---|---|---|
| FR-1.1 | Users sign in exclusively via GitHub OAuth (Supabase Auth); no password login. | ✅ |
| FR-1.2 | API requests carry a Supabase JWT that the backend validates **fail-closed**: HS256 with `SUPABASE_JWT_SECRET`, expiry check, and JWKS/RS256 fallback. Invalid/missing token → 401; auth not configured → 503 (never open access). | ✅ |
| FR-1.3 | Frontend only renders authenticated workspaces when a valid session exists; sign-out clears local session state. | ✅ |
| FR-1.4 | Supabase RLS is deny-all; the backend service role is the only privileged data path. | ✅ |

**Acceptance:** unauthenticated `POST /api/v1/runs` returns 401; expired/tampered tokens rejected; GitHub sign-in succeeds from every registered frontend origin.

### FR-2 — Repository & Workspace Management

| ID | Requirement | Status |
|---|---|---|
| FR-2.1 | Users can shallow-clone a GitHub repository into a workspace via `POST /api/v1/repos/clone` (body `{owner, name}` → returns `{id, name, path, branch}`). | ✅ |
| FR-2.2 | Workspace ids are deterministic (`gh-{owner}-{name}`); clone directories live under `cloned_repos/{owner}__{name}`. | ✅ |
| FR-2.3 | Workspaces survive backend restarts: on startup the server re-adopts existing clone directories (self-healing mapping) and drops stale entries. | ✅ |
| FR-2.4 | Tree and file content are served via `GET /api/v1/workspaces`, `/tree`, `/file` with path-traversal rejection (ids containing `..` or escaping the workspace root are rejected). | ✅ |
| FR-2.5 | Browsing a non-git workspace (e.g., demo fixture) works and reports honestly that diffs are unavailable. | ✅ |

**Acceptance:** clone → restart backend → workspace list still contains the clone; `?path=../../etc` is rejected with 4xx.

### FR-3 — Agent Task Execution

| ID | Requirement | Status |
|---|---|---|
| FR-3.1 | `POST /api/v1/agent/analyze` runs a stateless single-agent loop over a workspace given a task prompt. | ✅ |
| FR-3.2 | `POST /api/v1/runs` executes the same loop **and persists** the run, its events, metrics, and token usage to Supabase. | ✅ |
| FR-3.3 | The loop follows a plan → act → verify cycle with an iteration budget; agent states: READY, THINKING, PLANNING, EXECUTING, TESTING, REPAIRING, COMPLETED, FAILED. | ✅ |
| FR-3.4 | The model may emit **multiple tool calls per response** (one JSON object per line); all are parsed and executed in the same iteration. A final-analysis object in the batch takes precedence. | ✅ |
| FR-3.5 | Repeating the identical tool call twice yields a corrective observation instead of a re-run; a third consecutive repeat forces honest completion. Test runs are exempt from the repeat guard. | ✅ |
| FR-3.6 | The agent's plan is preserved to the run (set on final answer, or synthesized when tests pass) and shown in the UI — never wiped. | ✅ |
| FR-3.7 | Failing tests trigger a repair loop (max 5 attempts) with failure history injected back into the prompt; each re-run increments the repair counter. | ✅ |
| FR-3.8 | A run only reports COMPLETED after a final full-suite verification passes; otherwise FAILED with diagnosis. | ✅ |
| FR-3.9 | System prompt contract documents batching, no-repeat behavior, and pressure to finalize within the iteration budget. | ✅ |
| FR-3.10 | Git branch creation/automation. | 🔄 |
| FR-3.11 | Conventional commit automation. | 🔄 |
| FR-3.12 | End-to-end GitHub Pull Request creation via API. | 🔜 |

### FR-4 — Agent Tools

| Tool | Requirement | Status |
|---|---|---|
| `list_files` | Directory listing confined to the workspace root. | ✅ |
| `read_file` | Line-limited file reader with size caps. | ✅ |
| `search_code` | Regex/text search across the workspace. | ✅ |
| `write_file` | Workspace-only file creation/edit with new-path validation. | ✅ |
| `apply_patch` | Real **unified-diff** application: multi-file, hunk-count parsing, offset ±5 plus full-file rescan, whitespace-tolerant context matching that preserves original indentation, `/dev/null` new-file support; **atomic** — a failed patch leaves the file untouched. | ✅ |
| `inspect_diff` | Real `git diff` / `git status` / `--numstat` output (capped ~12k chars) with honest messaging on non-git workspaces. | ✅ |
| `run_tests` | Executes only allow-listed test commands in a sandbox: 60s timeout, SIGALRM, 100KB output cap, sanitized environment. | ✅ |

**Acceptance:** applying a malformed or context-mismatching patch returns an error and byte-identical file; a valid multi-file patch applies atomically; `run_tests` refuses non-test commands.

### FR-5 — Run History & Events

| ID | Requirement | Status |
|---|---|---|
| FR-5.1 | `GET /api/v1/runs`, `/runs/{id}`, `/runs/{id}/events` return persisted history for the authenticated user. | ✅ |
| FR-5.2 | Every event carries `tool_name` / `observation` merged into its stored payload so the timeline can label tool activity. | ✅ |
| FR-5.3 | Events update the UI timeline in near-real-time during a run. | ✅ |

### FR-6 — Prompt Intelligence

| ID | Requirement | Status |
|---|---|---|
| FR-6.1 | Prompt Score: 6-dimension rubric scoring 0–100 shown next to the composer. | ✅ |
| FR-6.2 | Prompt Lab: concrete improvement suggestions and a rewrite assistant; score is not a hard gate. | ✅ |

### FR-7 — Analytics & Insights

| ID | Requirement | Status |
|---|---|---|
| FR-7.1 | Token estimation pre-flight and post-run usage/cost breakdown (dashboard + charts). | ✅ |
| FR-7.2 | Agent efficiency metrics: runtime, LLM calls, tool calls, repair iterations. | ✅ |
| FR-7.3 | Repository architecture map: interactive dependency/module graph of the workspace. | ✅ |

### FR-8 — User Interface

| ID | Requirement | Status |
|---|---|---|
| FR-8.1 | Marketing landing page and GitHub-only login page (split layout: form + showcase). | ✅ |
| FR-8.2 | Workspace shell with views: repositories, files, agent, changes, tests, architecture, prompt, usage, efficiency. | ✅ |
| FR-8.3 | Agent panel with tabs ACTIVITY / CHANGES / TESTS / VERIFICATION, live status pill, event counter, plan display, reset & view-changes actions. | ✅ |
| FR-8.4 | Dark / light theme with persistence. | ✅ |
| FR-8.5 | Multi-model selection (incl. Super/Nano variants) from the composer. | ✅ |

## 2. Non-Functional Requirements

### NFR-1 — Security

- **Workspace confinement:** every filesystem operation resolves inside the workspace root; traversal (`..`, absolute paths, symlinks escaping root) rejected (`test_workspace_security.py`).
- **Command allow-list:** only known test runners can execute; environment sanitized; timeouts enforced.
- **Secrets:** never committed, never logged; `.env` gitignored; frontend config baked at build from Vercel Config vars.
- **CORS:** explicit origin allow-list (`FRONTEND_ORIGINS`), one entry per deployed frontend origin.
- **Auth:** fail-closed by construction (FR-1.2).

### NFR-2 — Reliability

- Atomic file patching (no partial writes).
- Backend restart tolerance: workspace mapping self-heals from disk (FR-2.3).
- Render idle sleep tolerated: requests auto-wake the service; clones are re-created on demand if the disk was wiped.
- A run never reports success without a passing final verification (FR-3.8).

### NFR-3 — Performance

- LLM temperature 0.3 (deterministic-leaning), `max_tokens` 2000.
- Diff output capped (~12k chars); file reads line-limited; test output capped at 100KB.
- Batched tool execution: N tool calls resolved in one iteration instead of N iterations.

### NFR-4 — Maintainability & Quality

- Backend: 113 pytest tests (`.venv/bin/python -m pytest backend/tests`) must pass; tests disable auth middleware automatically via `conftest.py`.
- Frontend: `npx tsc -b`, `npx oxlint`, `npm run build` must all pass with 0 errors.
- Docs (README, this set) kept synchronized with reality — unfinished features are never marked complete.

### NFR-5 — Compatibility & Ports

- Frontend is SPA-served (Vercel rewrite: all routes → `index.html`).
- Backend targets Python 3.11+, FastAPI; frontend targets evergreen browsers (React 19 / Vite 8).
- `VITE_*` variables are build-time only and must be Config (not Secret) on Vercel.

## 3. Environment & Configuration Requirements

| Variable | Where | Purpose |
|---|---|---|
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` | backend `.env` / Render | PostgREST persistence |
| `SUPABASE_JWT_SECRET` | backend | HS256 JWT validation |
| `NEBIUS_API_KEY` / LLM endpoint config | backend `.env` | LLM calls |
| `FRONTEND_ORIGINS` | Render | CORS allow-list (comma-separated) |
| `VITE_API_BASE` | Vercel Config | API base baked into the bundle |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Vercel Config | Browser Supabase client |

Supabase dashboard: OAuth redirect URLs must include every deployed frontend origin.

## 4. Out of Scope (current release)

- Multi-user collaboration on one workspace; workspace sharing.
- Non-GitHub providers (GitLab/Bitbucket).
- Arbitrary shell access for the agent (by design — tools are the only capability).
- Self-hosted LLMs (Nebius-hosted Nemotron only).
