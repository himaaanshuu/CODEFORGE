# ⚒️ CodeForge AI

### Autonomous Software Engineering Agent

> **CodeForge doesn't just write code. It proves its work.**

CodeForge AI is an autonomous software-engineering agent designed to understand real codebases, reason about developer requirements, modify code, run tests, diagnose failures, repair them iteratively, and verify the final result before delivering changes through GitHub.

---

## ✦ The Idea

```text
USER TASK
    │
    ▼
UNDERSTAND
    │
    ▼
EXPLORE REPOSITORY
    │
    ▼
PLAN
    │
    ▼
MODIFY
    │
    ▼
TEST
    │
    ├──────── PASS ────────► VERIFY
    │                         │
    │                         ▼
    │                    GIT + GITHUB
    │                         │
    │                         ▼
    │                       PR
    │                         │
    │                         ▼
    │                    VERIFIED ✓
    │
    └──────── FAIL ────────► DIAGNOSE
                              │
                              ▼
                            REPAIR
                              │
                              └──────► TEST AGAIN
```

## 🚀 Why CodeForge?

Most AI coding tools focus on generating code.

**CodeForge focuses on engineering outcomes.**

| Principle | What CodeForge does |
|---|---|
| 🧠 Reason | Understands the task and repository before editing |
| 🔎 Explore | Finds relevant files, modules, tests and dependencies |
| 🛠️ Act | Uses controlled tools to modify the codebase |
| 🧪 Test | Runs real tests instead of assuming correctness |
| 🔧 Repair | Diagnoses and fixes failures iteratively |
| 🔍 Prove | Produces evidence that the implementation works |
| 🚀 Deliver | Creates a branch, commit and Pull Request |

---

# 🧭 Core Workflow

```mermaid
flowchart TD
    A["👤 Developer"] --> B["📝 Coding Task"]
    B --> C["🧠 Understand"]
    C --> D["🔎 Explore Repository"]
    D --> E["📋 Create Plan"]
    E --> F["🛠️ Modify Code"]
    F --> G["🧪 Run Tests"]
    G --> H{"Tests Pass?"}
    H -->|Yes| I["🔍 Verify"]
    H -->|No| J["🧠 Diagnose Failure"]
    J --> K["🔧 Repair Code"]
    K --> G
    I --> L["🌿 Create Git Branch"]
    L --> M["💾 Commit Changes"]
    M --> N["🚀 Push Branch"]
    N --> O["🔀 Create Pull Request"]
    O --> P["✅ VERIFIED"]
```

---

# 🏗️ System Architecture

```mermaid
flowchart TB
    User["👤 Developer"]
    Frontend["CODEFORGE UI<br/>React + Vite + TypeScript"]
    Backend["CODEFORGE API<br/>FastAPI + Python"]
    Agent["AGENT ORCHESTRATOR"]
    LLM["NVIDIA Nemotron 3 Ultra<br/>550B A55B"]
    Nebius["Nebius Token Factory"]
    Tools["TOOL REGISTRY"]
    Workspace["WORKSPACE"]
    Execution["CONTROLLED EXECUTION"]
    Tests["TEST RUNNER"]
    Git["GIT"]
    GitHub["GitHub API"]

    User --> Frontend
    Frontend --> Backend
    Backend --> Agent
    Agent --> LLM
    LLM --> Nebius
    Nebius --> LLM
    Agent --> Tools
    Tools --> Workspace
    Tools --> Execution
    Execution --> Tests
    Agent --> Git
    Git --> GitHub
    Tests --> Agent
    Workspace --> Agent
    Agent --> Backend
    Backend --> Frontend
```

---

# 🧠 Agent Architecture

CodeForge separates **reasoning** from **execution**.

```mermaid
flowchart LR
    Task["Developer Task"]
    Context["Repository Context"]
    Agent["Agent Orchestrator"]
    Model["Nemotron 3 Ultra"]
    Registry["Tool Registry"]
    Tools["Controlled Tools"]
    Result["Evidence"]

    Task --> Agent
    Context --> Agent
    Agent --> Model
    Model --> Agent
    Agent --> Registry
    Registry --> Tools
    Tools --> Agent
    Agent --> Result
```

### Agent responsibilities

```text
AGENT
│
├── Task Understanding
├── Repository Exploration
├── Context Selection
├── Planning
├── Tool Selection
├── Code Modification
├── Test Execution
├── Failure Diagnosis
├── Autonomous Repair
├── Verification
└── Git Delivery
```

---

# 🛠️ Tool Architecture

```text
TOOL REGISTRY
│
├── Repository Tools
│   ├── list_files
│   ├── read_file
│   └── search_code
│
├── Modification Tools
│   ├── apply_patch
│   ├── write_file
│   └── inspect_diff
│
├── Testing Tools
│   └── run_tests
│
├── Git Tools
│   ├── git_diff
│   ├── git_branch
│   ├── git_commit
│   └── git_push
│
└── GitHub Tools
    └── create_pull_request
```

---

# 🔧 Autonomous Repair Loop

The defining capability of CodeForge is the:

**TEST → DIAGNOSE → REPAIR → VERIFY**

loop.

```mermaid
flowchart TD
    A["🛠️ Apply Implementation"] --> B["🧪 Run Tests"]
    B --> C{"All Tests Pass?"}
    C -->|YES| D["🔍 Verification"]
    C -->|NO| E["📋 Capture Failure"]
    E --> F["🧠 Diagnose Root Cause"]
    F --> G["🔧 Generate Repair"]
    G --> H["🛠️ Apply Repair"]
    H --> I{"Loop Detected?"}
    I -->|YES| J["❌ Stop Safely"]
    I -->|NO| B
    D --> K["✅ VERIFIED"]
```

### Example

```text
Initial implementation
        │
        ▼
27 passed / 2 failed
        │
        ▼
Diagnose
        │
        ▼
Root cause identified
        │
        ▼
Repair #1
        │
        ▼
31 passed / 0 failed
        │
        ▼
VERIFY
        │
        ▼
VERIFIED ✓
```

---

# 🔀 GitHub Workflow

CodeForge is designed around a safe Git workflow.

```mermaid
flowchart LR
    A["GitHub Repository"]
    B["CodeForge Workspace"]
    C["Agent Changes"]
    D["Feature Branch"]
    E["Commit"]
    F["Push"]
    G["Pull Request"]
    H["Developer Review"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
```

### Default philosophy

```text
❌ Agent → main

Instead:

Agent
  ↓
feature/codeforge/<task>
  ↓
commit
  ↓
push
  ↓
Pull Request
  ↓
Developer Review
```

---

# 📊 Feature Status

> Keep this table synchronized with the actual repository. Do not mark unfinished functionality as complete.

| Feature | Status | Notes |
|---|---|---|
| React + Vite frontend | ✅ Available | React 19, TypeScript, Tailwind CSS, Lucide Icons |
| FastAPI backend | ✅ Available | Modular architecture, ASGI hot-reload, CORS |
| Nemotron 3 Ultra integration | ✅ Available | `nvidia/nemotron-3-ultra-550b-a55b` via Nebius |
| Nebius Token Factory integration | ✅ Available | OpenAI-compatible streaming & completions |
| Repository exploration | ✅ Available | Path-traversal safe exploration suite |
| `list_files` | ✅ Available | Traversal-guarded directory lister |
| `read_file` | ✅ Available | Safe line-limited file reader with size caps |
| `search_code` | ✅ Available | Regex/text search across workspace |
| Workspace path security | ✅ Available | Chroot-style boundary enforcement & path checks |
| Agent state management | ✅ Available | Multi-phase state machine & iteration control |
| Structured agent events | ✅ Available | Real-time event timeline & streaming payloads |
| Code modification | ✅ Available | Controlled modification with path verification |
| `apply_patch` | ✅ Available | Unified diff patcher with atomic application |
| `inspect_diff` | ✅ Available | Workspace diff inspection & hunk parsing |
| `write_file` | ✅ Available | Safe workspace-only file creation & editing |
| Test execution (`run_tests`) | ✅ Available | Sandboxed execution policy with strict command filtering |
| Sandboxed test runner | ✅ Available | 60s timeout, SIGALRM, 100KB limits, env sanitization |
| Autonomous repair loop | ✅ Available | Max 5 repair attempts, failure history tracking |
| Failure diagnosis | ✅ Available | LLM root-cause analysis & regression prevention |
| Final verification | ✅ Available | Full test suite re-verification gate before success |
| GitHub OAuth authentication | ✅ Available | Supabase Auth with HS256 JWT validation & fail-closed |
| Supabase run persistence | ✅ Available | PostgREST run storage, event timelines & metrics |
| GitHub repo cloning | ✅ Available | `/api/v1/repos/clone` shallow clone into workspace |
| Prompt Score | ✅ Available | 6-dimension rubric quality scoring (0–100) |
| Prompt Improvement | ✅ Available | Prompt Lab suggestion engine & rewrite assistant |
| Token estimation | ✅ Available | Heuristic pre-flight input/output token estimator |
| Token usage analytics | ✅ Available | Usage dashboard with cost breakdown & charts |
| Agent efficiency metrics | ✅ Available | Runtime, LLM calls, repair iterations, tool calls |
| Repository architecture map | ✅ Available | Interactive visual dependency & module graph |
| Dark / Light mode | ✅ Available | Editorial warm dark & clean light theme with persistence |
| Git branch automation | 🔄 In Development | Automated feature branch creation |
| Git commit automation | 🔄 In Development | Automated conventional commit creation |
| Pull Request creation | 🔜 Planned | End-to-end GitHub PR creation via API |

---

# 🗺️ Product Roadmap

```mermaid
flowchart LR
    A["Phase 1<br/>Foundation"]
    B["Phase 2<br/>LLM"]
    C["Phase 3<br/>Agent"]
    D["Phase 4<br/>Code Modification"]
    E["Phase 5<br/>Testing"]
    F["Phase 6<br/>Autonomous Repair"]
    G["Phase 7<br/>GitHub"]
    H["Phase 8<br/>Product UX"]
    I["Phase 9<br/>Persistence"]
    J["Hackathon Ready"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
```

---

# 🖥️ Dashboard Architecture

CodeForge is designed as a developer workspace rather than a generic AI chatbot.

```text
CODEFORGE AI
│
├── WORKSPACE
│   ├── Repository
│   ├── Files
│   ├── Agent
│   ├── Changes
│   ├── Tests
│   └── Architecture
│
├── INSIGHTS
│   ├── Prompt Lab
│   ├── Usage
│   └── Efficiency
│
└── SETTINGS
    ├── Account
    ├── GitHub
    ├── Model
    ├── Theme
    └── Security
```

---

# 🎨 Main Workspace

```text
┌───────────────────────────────────────────────────────────────┐
│ CODEFORGE AI      repo / branch      STATUS     NEMOTRON     │
├──────────────┬────────────────────────────────────────────────┤
│              │                                                │
│ WORKSPACE    │              AGENT WORKSPACE                   │
│              │                                                │
│ Repository   │       WHAT SHOULD I CHANGE?                   │
│ Files        │                                                │
│ Agent        │       Describe your coding task.               │
│ Changes      │                                                │
│ Tests        │       ┌────────────────────────────────────┐   │
│ Architecture │       │                                    │   │
│              │       │ Task description                   │   │
│ INSIGHTS     │       │                                    │   │
│              │       └────────────────────────────────────┘   │
│ Prompt Lab   │                                                │
│ Usage        │                 RUN AGENT                      │
│ Efficiency   │                                                │
│              │                                                │
└──────────────┴────────────────────────────────────────────────┘
```

---

# ✍️ Prompt Intelligence

CodeForge is designed to help developers write better engineering tasks.

## Prompt Score

```text
PROMPT QUALITY
│
├── Clarity
├── Specificity
├── Context
├── Constraints
├── Testability
└── Token Efficiency
```

Example:

```text
PROMPT SCORE

82 / 100

✓ Clear objective
✓ Relevant context
✓ Test requirement included
△ Missing edge cases
△ Could specify affected modules
```

> Prompt Score is a quality estimate, not a guarantee of agent success.

---

# 🪄 Prompt Improvement

Example transformation:

```text
Before:

"add authentication"
```

```text
After:

Implement JWT-based authentication for the existing
login flow.

Requirements:
- Preserve current login behavior.
- Add access and refresh tokens.
- Protect authenticated API routes.
- Store secrets through environment variables.
- Add authentication middleware.
- Add unit and integration tests.
- Do not expose credentials.
- Keep the existing API contract unchanged.
```

---

# 🪙 Token Intelligence

CodeForge distinguishes between **estimated** and **actual** usage.

### Before execution

```text
Estimated Input       ~8.9K
Estimated Output      ~2.4K
Estimated Total       ~11.3K
```

### After execution

```text
Actual Input          28,120
Actual Output         10,301
Actual Total          38,421
```

Actual usage should come from provider/model response metadata whenever available.

---

# 💰 Token Cost Model

```text
Input Cost
=
Input Tokens / 1,000,000
× Input Price

Output Cost
=
Output Tokens / 1,000,000
× Output Price

Total Cost
=
Input Cost + Output Cost
```

Example:

```text
Input Tokens       28,120
Output Tokens      10,301

Input Cost         $X.XXXX
Output Cost        $X.XXXX

TOTAL              $X.XXXX
```

> Pricing values should come from the configured provider/model pricing rather than fake hardcoded values.

---

# 📈 Token Breakdown

```text
TOKEN USAGE
│
├── Repository Exploration
├── Context Construction
├── Planning
├── Code Modification
├── Test Diagnosis
├── Repair Attempts
└── Verification
```

This makes it possible to understand where the agent spends its reasoning budget.

---

# ⚡ Agent Efficiency

CodeForge focuses on measurable execution metrics rather than an unexplained AI score.

```text
┌─────────────────────────────────────────────┐
│              AGENT EFFICIENCY               │
├─────────────────────────────────────────────┤
│                                             │
│  38.4K       8          14          1       │
│  Tokens    LLM Calls   Tool Calls   Repair  │
│                                             │
│  42s        31/31       100%                 │
│  Runtime    Tests        Verified            │
│                                             │
└─────────────────────────────────────────────┘
```

Potential measurable metrics:

```text
• Total tokens
• Input tokens
• Output tokens
• LLM calls
• Tool calls
• Test runs
• Repair attempts
• Execution time
• Files changed
• Tests passed
• Tests failed
• Final verification status
```

---

# 🧬 Repository Architecture Map

A planned developer-insight feature is an interactive code architecture graph.

```mermaid
graph TD
    Main["main.py"]
    API["API Routes"]
    Agent["Agent"]
    LLM["LLM Client"]
    Tools["Tool Registry"]
    Repo["Repository"]
    Execution["Execution"]
    Tests["Tests"]
    Git["Git"]

    API --> Agent
    Agent --> LLM
    Agent --> Tools
    Tools --> Repo
    Tools --> Execution
    Execution --> Tests
    Agent --> Git
    Tests --> Agent
    API --> Repo
```

### Potential node types

```text
Entry Points
Modules
Services
Models
Routes
Repositories
Utilities
Tests
Configuration
```

### Potential relationships

```text
imports
calls
depends-on
tested-by
extends
implements
```

---

# 🔐 Security Model

CodeForge treats agent execution as privileged.

```mermaid
flowchart TD
    Request["User Request"]
    Policy["Execution Policy"]
    Workspace["Workspace Boundary"]
    Tools["Allowed Tools"]
    Runner["Controlled Runner"]
    Result["Sanitized Result"]

    Request --> Policy
    Policy --> Workspace
    Workspace --> Tools
    Tools --> Runner
    Runner --> Result
```

### Security principles

- Workspace-scoped file access
- Path traversal protection
- Absolute path restrictions
- `.git` protection
- File size limits
- Controlled command execution
- Execution timeouts
- Output limits
- Environment sanitization
- No unrestricted shell access
- No unrestricted network access
- Secrets kept outside source code
- API keys stored through environment variables
- GitHub credentials handled server-side
- Pull Requests preferred over direct main-branch modification

---

# 🧰 Technology Stack

## Frontend

```text
React
TypeScript
Vite
Framer Motion
Lucide Icons
CSS
```

## Backend

```text
Python
FastAPI
Pydantic
```

## AI

```text
NVIDIA Nemotron 3 Ultra 550B A55B
Nebius Token Factory
OpenAI-compatible API
```

## Development

```text
Git
GitHub
Pytest
Node.js
npm / pnpm
```

## Planned Infrastructure

```text
Supabase Auth
Supabase PostgreSQL
Supabase Realtime
GitHub API
```

---

# 🧠 NVIDIA + Nebius Architecture

CodeForge uses NVIDIA's Nemotron model through Nebius infrastructure.

```mermaid
flowchart LR
    CodeForge["CodeForge Agent"]
    API["OpenAI-Compatible API"]
    Nebius["Nebius Token Factory"]
    Nemotron["NVIDIA Nemotron 3 Ultra<br/>550B A55B"]

    CodeForge --> API
    API --> Nebius
    Nebius --> Nemotron
    Nemotron --> Nebius
    Nebius --> API
    API --> CodeForge
```

### Model configuration

```env
NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
```

> Never commit your actual `NEBIUS_API_KEY`.

---

# 📁 Project Structure

```text
CODEFORGE/
│
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI application & API endpoints
│   │   ├── config.py                # Environment & configuration loader
│   │   ├── auth_middleware.py       # JWT authentication & fail-closed middleware
│   │   │
│   │   ├── agent/                   # Agent orchestration
│   │   │   ├── agent.py             # Main run loop, autonomous repair & verification
│   │   │   ├── models.py            # Pydantic models for events, states & requests
│   │   │   ├── prompts.py           # System prompts & developer instructions
│   │   │   └── state.py             # Agent runtime state & iteration tracker
│   │   │
│   │   ├── execution/               # Sandboxed test execution
│   │   │   ├── models.py            # Execution models & result schemas
│   │   │   └── runner.py            # Safe runner with timeout & env sanitization
│   │   │
│   │   ├── llm/                     # Nebius Token Factory client
│   │   │   ├── client.py            # NVIDIA Nemotron LLM integration
│   │   │   └── models.py            # Request/response schemas
│   │   │
│   │   ├── repository/              # Workspace boundary safety
│   │   │   └── workspace.py         # Path validation & directory navigation
│   │   │
│   │   └── tools/                   # Controlled agent tools
│   │       ├── base.py              # Base tool contract
│   │       ├── registry.py          # Tool registration & discovery
│   │       ├── repository_tools.py  # list_files, read_file, search_code
│   │       ├── modification_tools.py# apply_patch, inspect_diff, write_file
│   │       └── execution_tools.py   # run_tests tool wrapper
│   │
│   ├── auth_dep.py                  # FastAPI auth dependency injection
│   ├── supabase_auth.py             # Supabase JWT token verification
│   ├── supabase_service.py          # Supabase PostgREST persistence service
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Copy to .env (gitignored)
│   │
│   └── tests/                       # 84 unit and integration tests (all passing)
│       ├── test_agent.py            # Agent loop, events & failure recovery
│       ├── test_api.py              # Workspace, file & tree API endpoints
│       ├── test_auth.py             # JWT signature, expiration, algorithm tests
│       ├── test_auth_middleware.py  # HTTP middleware 401/503 & CORS verification
│       ├── test_llm.py              # LLM client & configuration tests
│       ├── test_supabase.py         # Persistence, RLS & user isolation
│       ├── test_workspace_security.py # Path traversal & boundary protection
│       └── conftest.py              # Test fixtures & mocks
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── agent/               # AgentStatus, TaskInput, PromptComposer, Activity
│   │   │   ├── code/                # DiffViewer, CodeViewer, HighlightedLine
│   │   │   ├── insights/            # PromptLab, UsageDashboard, Efficiency, ArchitectureMap
│   │   │   ├── intro/               # IntroAnimation
│   │   │   ├── layout/              # AppShell, Header, Sidebar
│   │   │   ├── repository/          # FileExplorer, RepoList
│   │   │   ├── run/                 # ChangesTab, TestsTab, VerificationTab
│   │   │   └── ui/                  # Button, Tabs, Alert, ScoreRing, ThemeToggle, Logo
│   │   ├── hooks/                   # useAgentRun, useAuth, useTheme
│   │   ├── lib/                     # agentClient, githubClient, promptScore, supabase
│   │   ├── screens/                 # Landing, Auth, GithubConnect, Workspace
│   │   ├── types/                   # TypeScript interfaces & types
│   │   ├── App.tsx                  # Root application router & screen manager
│   │   ├── index.css                # Editorial styling, CSS variables & typography
│   │   └── main.tsx                 # React DOM root entry
│   │
│   ├── .env.local.example           # Copy to .env.local (gitignored)
│   ├── package.json
│   ├── tailwind.config.cjs
│   └── vite.config.ts
│
├── supabase/
│   └── migrations/
│       └── 0001_init.sql            # PostgreSQL schema: runs, events, usage, RLS
│
├── pytest.ini                       # testpaths = backend/tests (run pytest from root)
├── .gitignore
├── LICENSE
└── README.md
```

> Keep this tree synchronized with the actual repository as development progresses.

---

# ⚙️ Installation

> All commands below assume your terminal is at the **repository root**
> (the folder containing `backend/`, `frontend/` and `pytest.ini`)
> unless a `cd` is shown explicitly.

## Prerequisites

```text
Python 3.11+  (verified with 3.14; backend/venv/ is the project virtualenv)
Node.js 20+   (verified with Node 24 + npm 11)
Git
Supabase project ( Auth + Postgres ) — dashboard access to copy API keys
Nebius Token Factory API key (for NVIDIA Nemotron)
```

---

# 📥 Clone

```bash
git clone https://github.com/himaaanshuu/CODEFORGE.git
cd CODEFORGE
```

The checkout directory is `CODEFORGE` (capital letters). All follow-up
commands use it as the working directory.

---

# 🐍 Backend Setup

From the repository root. Skip the `venv` creation if `backend/venv/`
already exists.

Windows (PowerShell):

```powershell
python -m venv backend\venv
.\backend\venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Git Bash / macOS / Linux:

```bash
python3 -m venv backend/venv
source backend/venv/Scripts/activate   # Windows Git Bash
# source backend/venv/bin/activate     # macOS / Linux
python -m pip install -r backend/requirements.txt
```

Then create the backend env file (see [Environment Variables](#-environment-variables)):

```powershell
copy backend\.env.example backend\.env
```

```bash
cp backend/.env.example backend/.env
```

---

# ⚛️ Frontend Setup

```bash
cd frontend
npm install
```

Then create the frontend env file (see below) before `npm run dev`:

```bash
cp .env.local.example .env.local   # Windows: copy .env.local.example .env.local
```

---

# 🔑 Environment Variables

### Backend (`backend/.env`)

Create it from the example (from the repo root):

```powershell
copy backend\.env.example backend\.env
```

```bash
cp backend/.env.example backend/.env
```

Then fill in (matches `backend/.env.example` exactly):

```env
# --- Nebius Token Factory (NVIDIA Nemotron) ---
NEBIUS_API_KEY=your_nebius_api_key
NEBIUS_BASE_URL=https://api.tokenfactory.nebius.com/v1
NEBIUS_MODEL=nvidia/Nemotron-3-Ultra-550b-a55b
DEBUG=False

# --- Supabase (Auth verification + PostgREST run persistence) ---
# Supabase Dashboard → Project Settings → API: Project URL, JWT secret, service_role key.
# Until these are set, protected /api/v1/* routes fail closed with 503 —
# auth is never silently bypassed.
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your_jwt_secret
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# --- CORS (comma-separated frontend origins) ---
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend (`frontend/.env.local`)

Create it from the example (from inside `frontend/`):

```bash
cp .env.local.example .env.local   # Windows: copy .env.local.example .env.local
```

```env
# Backend API base (no trailing slash required; /api suffix included)
VITE_API_BASE=http://localhost:8000/api/v1

# Supabase project config (Dashboard → Project Settings → API → Project URL + anon public key)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_public_key
```

> **Security note:** `backend/.env` (root `.gitignore`) and
> `frontend/.env.local` (`frontend/.gitignore` → `*.local`) are gitignored.
> Never commit them. `NEBIUS_API_KEY` and `SUPABASE_SERVICE_ROLE_KEY`
> are server-only — never put them in `VITE_*` variables.

### Supabase database

Apply the schema once per project (Supabase Dashboard → SQL Editor → paste & run):

```text
supabase/migrations/0001_init.sql   # runs, events, usage tables + RLS
```

---

# ▶️ Running CodeForge

## Start Backend

From the **repository root** with the venv active (required — `main.py`
uses `from .. import ...` relative imports, so the module path must be
`backend.app.main`):

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload --port 8000
```

```bash
source backend/venv/Scripts/activate   # Windows Git Bash
# source backend/venv/bin/activate     # macOS / Linux
python -m uvicorn backend.app.main:app --reload --port 8000
```

> ❌ Do **not** run `uvicorn app.main:app` from inside `backend/` — it fails
> with `ImportError: attempted relative import beyond top-level package`.

- API Base: `http://localhost:8000`
- Health check: `http://localhost:8000/health`
- Interactive Swagger docs: `http://localhost:8000/docs`

---

## Start Frontend

From `frontend/`:

```bash
npm run dev
```

- Web UI: `http://localhost:5173`

---

# 🧪 Testing & Validation

### Backend Test Suite

`pytest.ini` sets `testpaths = backend/tests`, so run pytest from the
**repository root** with the venv Python (plain `pytest` / `cd backend`
will not resolve the suite correctly):

```powershell
.\backend\venv\Scripts\Activate.ps1
python -m pytest -v
```

```bash
python -m pytest -v
```

**84 / 84 tests passing:**

| Test Suite | Tests | Scope |
|---|---|---|
| `tests/test_agent.py` | 9 | Agent loop, state machine, lifecycle events |
| `tests/test_api.py` | 15 | Workspaces, tree, file, clone, runs endpoints |
| `tests/test_auth.py` | 18 | Real HS256 JWT validation, expiration, algorithm whitelist |
| `tests/test_auth_middleware.py` | 9 | Pre-routing 401/503 fail-closed logic & CORS |
| `tests/test_llm.py` | 4 | Nebius Token Factory client & model configuration |
| `tests/test_supabase.py` | 17 | Run persistence, ownership isolation & RLS policies |
| `tests/test_workspace_security.py` | 12 | Path traversal prevention & chroot boundaries |

### Frontend Build & Typecheck

```bash
cd frontend
npm run lint     # oxlint (0 errors)
npm run build    # tsc -b && vite build (production bundle validation)
```

---

# 🧑‍💻 Using CodeForge

## 1. Open CodeForge

```text
http://localhost:5173
```

## 2. Connect GitHub

Planned product flow:

```text
Sign In
   ↓
Connect GitHub
   ↓
Authorize CodeForge
```

## 3. Choose a Project

```text
┌─────────────────────────────┐
│       SELECT PROJECT        │
├─────────────────────────────┤
│                             │
│  Existing Repository        │
│  └── Select GitHub Repo     │
│                             │
│             OR              │
│                             │
│  New Project                │
│  └── Start From Scratch     │
│                             │
└─────────────────────────────┘
```

## 4. Describe the Task

Example:

```text
Add JWT authentication while preserving
the existing login flow.

Requirements:
- Add access and refresh tokens
- Protect authenticated routes
- Add tests
- Keep existing API behavior
- Do not expose secrets
```

## 5. Run Agent

```text
UNDERSTAND
     ↓
EXPLORE
     ↓
PLAN
     ↓
MODIFY
     ↓
TEST
     ↓
REPAIR
     ↓
VERIFY
```

## 6. Review Evidence

Example final result:

```text
VERIFIED ✓

Files changed:       7
Tests executed:      31
Tests passed:        31
Repair attempts:     1
LLM calls:           8
Tool calls:          14
Tokens used:         38.4K

Git branch:          feature/jwt-auth
Commit:              abc1234
Pull Request:        #42
```

> Only show metrics that actually came from the run.

---

# 🌿 Fork Guide

### 1. Fork the repository

Click **Fork** on GitHub.

### 2. Clone your fork

```bash
git clone https://github.com/himaaanshuu/CODEFORGE.git
cd CODEFORGE
```

### 3. Add upstream

```bash
git remote add upstream https://github.com/himaaanshuu/CODEFORGE.git
```

Check:

```bash
git remote -v
```

Expected:

```text
origin    → your fork
upstream  → original repository
```

### 4. Create a branch

```bash
git checkout -b feature/my-feature
```

### 5. Make changes

Run tests and builds.

### 6. Commit

```bash
git add .
git commit -m "feat: add my feature"
```

### 7. Push

```bash
git push -u origin feature/my-feature
```

### 8. Open a Pull Request

Create the PR from your fork to the original repository.

---

# 🔄 Development Workflow

```mermaid
flowchart LR
    A["Issue / Idea"]
    B["Create Branch"]
    C["Implement"]
    D["Run Tests"]
    E["Review Diff"]
    F["Commit"]
    G["Push"]
    H["Pull Request"]
    I["Review"]
    J["Merge"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
```

Recommended branches:

```text
feature/<name>
fix/<name>
refactor/<name>
docs/<name>
test/<name>
```

---

# 🧪 Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> Ready
    Ready --> Understanding
    Understanding --> Exploring
    Exploring --> Planning
    Planning --> Modifying
    Modifying --> Testing

    Testing --> Verified: PASS
    Testing --> Diagnosing: FAIL

    Diagnosing --> Repairing
    Repairing --> Testing

    Verified --> GitDelivery
    GitDelivery --> Completed

    Diagnosing --> Failed: Max attempts
    Repairing --> Failed: Unsafe state

    Completed --> [*]
    Failed --> [*]
```

---

# 📡 Agent Events

Typical lifecycle:

```text
agent_started
      ↓
thinking
      ↓
tool_requested
      ↓
tool_completed
      ↓
analysis_updated
      ↓
tool_requested
      ↓
tool_completed
      ↓
analysis_updated
      ↓
agent_completed
```

Failure:

```text
agent_started
      ↓
thinking
      ↓
tool_requested
      ↓
tool_completed
      ↓
agent_failed
```

These events allow the frontend to render a live agent activity stream.

---

# 🖥️ Frontend State Model

```text
READY
  ↓
ANALYZING
  ↓
PLANNING
  ↓
MODIFYING
  ↓
TESTING
  ↓
REPAIRING
  ↓
VERIFYING
  ↓
COMPLETED
```

Failure can occur from any active stage:

```text
ANALYZING ───→ FAILED
PLANNING ─────→ FAILED
MODIFYING ────→ FAILED
TESTING ──────→ FAILED
REPAIRING ────→ FAILED
VERIFYING ────→ FAILED
```

---

# 🧩 API Surface

All `/api/v1/*` routes require a verified Supabase access token (`Authorization: Bearer <token>`). Missing/invalid tokens fail closed with `401 Unauthorized`; unconfigured Supabase credentials return `503 Service Unavailable`.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/` | Public | Service health & welcome message |
| `GET` | `/health` | Public | Uptime & health check |
| `POST` | `/api/v1/llm/generate` | Protected | Direct generation via NVIDIA Nemotron (Nebius) |
| `POST` | `/api/v1/repos/clone` | Protected | Clone GitHub repository into backend workspace |
| `GET` | `/api/v1/workspaces` | Protected | List registered workspaces with active git branch |
| `GET` | `/api/v1/workspaces/{id}/tree` | Protected | Safe directory tree (sensitive dirs skipped) |
| `GET` | `/api/v1/workspaces/{id}/file` | Protected | Read file contents (traversal/sensitive guarded) |
| `POST` | `/api/v1/agent/analyze` | Protected | Run autonomous agent loop on workspace task |
| `POST` | `/api/v1/runs` | Protected | Execute agent and persist run, metrics & events |
| `GET` | `/api/v1/runs` | Protected | Caller's persisted runs (newest first, cursor paginated) |
| `GET` | `/api/v1/runs/{run_id}` | Protected | Fetch run details and execution status |
| `GET` | `/api/v1/runs/{run_id}/events` | Protected | Paginated event timeline of an agent run |

---

# 📦 Example Agent Request

```json
{
  "task": "Add JWT authentication while preserving the existing login flow.",
  "repository": "codeforge-demo"
}
```

Illustrative result:

```json
{
  "status": "completed",
  "summary": "Implemented JWT authentication.",
  "files_changed": [],
  "tests": {
    "passed": 31,
    "failed": 0
  },
  "repair_attempts": 1,
  "verified": true
}
```

> Example payloads are illustrative. Actual schemas should match the backend models.

---

# 🔭 Future Features

```text
                    CODEFORGE
                        │
        ┌───────────────┼────────────────┐
        │               │                │
      AGENT          INSIGHTS         PLATFORM
        │               │                │
        ├─ GitHub       ├─ Usage         ├─ Auth
        ├─ PRs          ├─ Tokens        ├─ Supabase
        ├─ Repair       ├─ Cost          ├─ Projects
        ├─ Verify       ├─ Efficiency    └─ Teams
        └─ Sandbox      └─ Prompt Lab
```

### Agent

- More repository tools
- Better context selection
- More execution environments
- Improved repair strategies
- Test-aware planning
- Safer autonomous execution
- Multi-language repository support

### GitHub

- Repository browsing
- Branch management
- Commit generation
- Pull Request creation
- PR review assistance
- PR comments
- Issue integration

### Intelligence

- Prompt Score
- Prompt Improvement
- Token estimation
- Actual token accounting
- Cost tracking
- Agent efficiency
- Repository architecture graph

### Platform

- Authentication
- Supabase persistence
- User projects
- Agent run history
- Realtime agent events
- Usage dashboard
- Team collaboration

---

# 🗺️ Long-Term Product Architecture

```mermaid
flowchart TB
    User["Developer"]
    Auth["Authentication"]
    UI["CodeForge Workspace"]
    Projects["Projects"]
    Runs["Agent Runs"]
    Agent["Agent Orchestrator"]
    Nemotron["Nemotron 3 Ultra"]
    Nebius["Nebius"]
    GitHub["GitHub"]
    Sandbox["Execution Sandbox"]
    Supabase["Supabase"]

    User --> Auth
    Auth --> UI
    UI --> Projects
    UI --> Runs
    Runs --> Agent
    Agent --> Nemotron
    Nemotron --> Nebius
    Agent --> Sandbox
    Agent --> GitHub
    Projects --> Supabase
    Runs --> Supabase
```

---

# 🎯 Hackathon Demo

The ideal CodeForge demo follows one complete engineering task.

## Demo Scenario

```text
Repository:
codeforge-demo

Task:

"Add JWT authentication while preserving
the existing login flow."
```

### Demo sequence

```text
01  Landing Page
        ↓
02  Sign In
        ↓
03  Connect GitHub
        ↓
04  Select Repository
        ↓
05  Submit Task
        ↓
06  Repository Exploration
        ↓
07  Implementation Plan
        ↓
08  Code Modification
        ↓
09  Tests Fail
        ↓
10  Autonomous Diagnosis
        ↓
11  Repair
        ↓
12  Tests Pass
        ↓
13  Verification
        ↓
14  Git Branch
        ↓
15  Commit
        ↓
16  Pull Request
        ↓
17  VERIFIED
```

---

# 🏆 The Killer Moment

The key CodeForge demo is not code generation.

It is autonomous recovery:

```text
TESTS
────────────────────────
27 passed
2 failed

        ↓

CODEFORGE
Diagnosing failure...

        ↓

Root cause identified.

        ↓

Repair attempt #1

        ↓

TESTS
────────────────────────
31 passed
0 failed

        ↓

VERIFICATION

✓ Implementation complete
✓ Tests passing
✓ Diff inspected
✓ No unresolved failures

        ↓

             VERIFIED ✓
```

---

# 🎨 Design Philosophy

CodeForge intentionally avoids the typical generic AI SaaS aesthetic.

```text
Avoid:
Purple
Neon
Huge gradients
Chatbot bubbles everywhere
Excessive glassmorphism
Unnecessary animation
```

Instead:

```text
Warm cream
Charcoal
Muted burgundy
Muted sage
Washed blue-gray

+

Editorial typography
Developer tooling density
Clear information hierarchy
Subtle motion
Readable code
```

The target feeling is:

```text
IDE
+
AI Agent
+
Engineering Dashboard
```

---

# ♿ Accessibility

CodeForge aims to support:

- Keyboard navigation
- Semantic HTML
- Visible focus states
- Accessible buttons
- Proper form labels
- Reduced-motion preferences
- Sufficient color contrast
- Screen-reader-friendly status messages
- Non-color-only status indicators

---

# 📈 Engineering Philosophy

```text
AI generation ≠ Software engineering
```

Software engineering requires:

```text
Understand
    +
Design
    +
Implement
    +
Test
    +
Debug
    +
Verify
    +
Deliver
```

CodeForge is designed around this complete lifecycle.

---

# 🤝 Contributing

Contributions are welcome.

### 1. Fork

Fork the repository from GitHub.

### 2. Clone

```bash
git clone https://github.com/himaaanshuu/CODEFORGE.git
```

### 3. Create a branch

```bash
git checkout -b feature/my-feature
```

### 4. Make changes

Follow the existing architecture and coding conventions.

### 5. Test

```bash
pytest
```

and:

```bash
npm run build
```

### 6. Commit

```bash
git add .
git commit -m "feat: describe your change"
```

### 7. Push

```bash
git push -u origin feature/my-feature
```

### 8. Open a Pull Request

Include:

```text
What changed?
Why?
How was it tested?
Any known limitations?
```

---

# 🛡️ Security

If you discover a security vulnerability, do not publicly disclose sensitive details in an issue. Contact the repository maintainer privately.

Never commit:

```text
.env
API keys
GitHub tokens
Supabase service role keys
Private credentials
Passwords
```

---

# 📜 License

CodeForge AI is released under the **MIT License**.

See [`LICENSE`](LICENSE) for the full license text.

---

# ⚒️ CodeForge AI

```text
┌───────────────────────────────────────────────┐
│                                               │
│              CODEFORGE AI                     │
│                                               │
│      Doesn't just write code.                 │
│              It proves its work.              │
│                                               │
│     UNDERSTAND → BUILD → TEST → REPAIR       │
│                    ↓                          │
│                 VERIFY                        │
│                    ↓                          │
│                GITHUB PR                      │
│                                               │
└───────────────────────────────────────────────┘
```

**Built with React · TypeScript · FastAPI · Python · NVIDIA Nemotron · Nebius · GitHub**

---

## ⭐ If CodeForge helps you

Star the repository, open an issue, contribute an improvement, or share the project.

**Build with confidence. Verify with evidence.**
