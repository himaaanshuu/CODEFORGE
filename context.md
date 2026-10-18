# Project Context — CodeForge AI

> What this project is, who it is for, and the state it is currently in.
> Complementary docs: [requirements.md](requirements.md) · [architecture.md](architecture.md) · [design.md](design.md)

## 1. The Idea

CodeForge AI is an **autonomous software engineering agent**. A user connects GitHub, points the agent at a repository, describes a change in plain language, and the agent plans, edits code, runs tests, and iterates until the task passes verification — showing every step in a live activity timeline.

It is not a chatbot wrapper: the product's value proposition is a **closed loop** (plan → edit → test → diagnose → repair → verify), with diff inspection and measurable efficiency at every stage.

## 2. Product Goals

1. **Autonomy** — one prompt in, verified code out; the agent self-repairs up to 5 times before failing honestly.
2. **Transparency** — every tool call, observation, plan step, and diff is visible; no silent edits.
3. **Safety** — the agent operates inside a chroot-style workspace boundary; no path traversal, no arbitrary command execution.
4. **Trust** — fail-closed authentication, atomic patches (a failed patch never leaves a half-written file), and a final full-suite verification gate before any run reports success.

## 3. Users & Primary Flow

| Persona | Need |
|---|---|
| Developer evaluating AI coding tools | Fast, trustworthy repo edits without pasting code into a chat window |
| Hackathon / demo audience | Instant "clone → prompt → diff → tests pass" story |

Primary flow:

1. Land on marketing page → **Sign in with GitHub** (Supabase OAuth).
2. Connect / clone a GitHub repository into a workspace.
3. Write a task prompt (Prompt Lab scores and improves it).
4. Run the agent → watch ACTIVITY timeline, CHANGES diff, TESTS results, VERIFICATION summary.
5. Review the diff, re-run, or start a new task.

## 4. Current State (as of this writing)

**Deployed and live:**

| Layer | URL |
|---|---|
| Frontend | `https://codeforge-delta-ivory.vercel.app` (older: `codeforge-pearl.vercel.app`) |
| Backend | `https://codeforge-ke01.onrender.com` (Render free tier) |
| DB / Auth | Supabase (Postgres + PostgREST + GitHub OAuth) |
| LLM | Nebius Token Factory, model `nvidia/Nemotron-3-Ultra-550b-a55b` |

**Implemented:** clone, workspace tree/file APIs, agent analyze, persistent runs + events, real unified-diff `apply_patch`, git-backed `inspect_diff`, sandboxed test runner, autonomous repair loop, batched tool-call parsing with repeat guard, prompt scoring/improvement, token & efficiency analytics, fit-to-view architecture map (whole file tree visible at once), marketing landing with pricing tiers (Free/Basic/Pro/Elite) and an in-app Docs handbook, clickable logo acting as a back button, dark/light themes.

**Not implemented:** git branch/commit automation (in development), GitHub PR creation (planned).

**Quality gates:** `backend/tests` — **113 pytest tests passing**; frontend `tsc` clean, `oxlint` clean, production build passes.

**Known operational constraints:**

- Render free tier sleeps when idle (first request is slow) and has an ephemeral disk — workspaces are re-cloned on demand, and workspace mapping self-heals by re-adopting existing clone directories after a restart.
- `VITE_*` build-time variables must be stored as Vercel **Config**, not Secrets (secrets are unavailable at build time).

## 5. Repository & Workflow Conventions

- Repo: `https://github.com/himaaanshuu/CODEFORGE.git`, branch `main`, working copy at `/Users/himanshu/EDITOR/codeforge-ai`.
- Never commit `.env` or print secret values; never commit unless explicitly asked.
- Commits are authored by the maintainer; the agent prepares changes and the maintainer commits/pushes (or explicitly delegates the push).
- Local dev:
  - Backend: `.venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000` (from repo root) → http://localhost:8000/health
  - Frontend: `npm run dev` (from `frontend/`) → http://localhost:5173
  - Logs: `/tmp/backend.log`, `/tmp/frontend.log`
- Verification commands: `.venv/bin/python -m pytest backend/tests`, `npx tsc -b`, `npx oxlint`, `npm run build` (last three from `frontend/`).

## 6. Naming & Brand

- Product name: **CodeForge AI** (wordmark: `CODEFORGE` bold + `AI` in accent).
- Logo: anvil mark served as `frontend/public/logo.png` (introduced by the "anvil rebrand" — the old `Logo.tsx` component was removed; screens render `<img src="/logo.png">` plus the wordmark).
- Design language: "editorial warm" — ink/cream base, burgundy, sage, denim, rust accents plus a dedicated green token for the READY state; serif display headings + mono labels. See [design.md](design.md).
