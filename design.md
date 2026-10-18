# Design — CodeForge AI

> UI/UX design system: tokens, typography, components, screen layouts, motion, and theming.
> Single source of truth for styling: `frontend/src/index.css` + `frontend/tailwind.config.cjs`.
> See [context.md](context.md) · [requirements.md](requirements.md) · [architecture.md](architecture.md).

## 1. Design Language — "Editorial Warm"

CodeForge looks like a printed technical journal, not a neon dev-tool dashboard: warm paper tones and near-black ink, serif-weight display headings, monospace labels, hairline borders instead of heavy cards, and a restrained burgundy/sage/denim/rust accent palette. Dark mode is a warm charcoal inversion, never pure black.

Principles:

1. **Hairlines over boxes** — separate with 1px borders; reserve shadows (`--shadow-raised`/`lift`) for true surfaces (panels, popovers).
2. **Type does the talking** — Space Grotesk for headings/labels, Manrope for body, JetBrains Mono for data, code, and IDs.
3. **Color is semantic** — burgundy = brand/action, sage = ok, rust = fail, denim = informational/neutral, muted = secondary text.
4. **Contrast first** — muted was darkened to meet AA on cream; `--on-accent` never flips with theme.

## 2. Tokens

### Color (CSS variables, exposed to Tailwind with alpha support)

| Group | Tokens |
|---|---|
| Ink (dark surfaces) | `--ink`, `--ink-soft`, `--ink-raised` |
| Cream (light surfaces) | `--cream`, `--cream-deep`, `--cream-muted` |
| Brand & accents | `--burgundy` (+ light/dark), `--sage` (+ light), `--green`, `--denim` (+ light), `--rust`, `--muted` |
| Borders | `--border` (13%), `--border-strong` (28%), `--border-on-ink` |
| Semantic (theme-aware) | `--bg`, `--surface`, `--fg`, `--subtle`, `--accent`, `--ok`, `--bad`, `--info`, `--raised`, `--line`, `--on-accent` |
| Code | `--diff-add-bg`, `--diff-del-bg`, `--syn-keyword` (burgundy), `--syn-string` (sage), `--syn-comment` (muted), `--syn-number` (rust), `--syn-fn` (denim) |

Tailwind classes map 1:1: `bg-surface`, `text-subtle`, `border-strong`, `text-accent`, `bg-ok`/`text-bad`, etc. Never hard-code hex values in components — use tokens.

### Typography

| Role | Font | Usage |
|---|---|---|
| Display | Space Grotesk (`font-display`) | Headings, buttons, tabs, wordmark |
| Sans | Manrope (`font-sans`) | Body copy (default) |
| Mono | JetBrains Mono (`font-mono`) | IDs, paths, timestamps, code, eyebrows, counters |

Conventions: uppercase mono micro-labels with tracking (`eyebrow` class); tabular numerals for counters/metrics (`tabular-nums`).

### Spacing, radius, shadow, motion

- Spacing scale: `--space-1…16` (0.25rem → 4rem); layout rhythm via Tailwind spacing utilities aligned to this scale.
- Radius: deliberately tiny — `rounded-xs` 2px, `rounded-sm` 4px, `rounded-md` 6px.
- Shadows: `shadow-raised` (default card), `shadow-lift` (focus/hover) — both intentionally small.
- Motion: `--dur-fast` 140ms, `--dur-base` 240ms, `--dur-slow` 480ms, `--ease-out` (0.22, 1, 0.36, 1); framer-motion used for list/tab transitions; `animate-pulse-dot` for active status dots. All motion respects `prefers-reduced-motion`.

## 3. Theming

- Two themes: **editorial warm dark** (default) and **clean light**, toggled via `data-theme` on the root element (`useTheme` hook, persisted in localStorage).
- Implementation: only the semantic block (`--bg`…`--on-accent`) plus accent/code derivations swap per theme; structural tokens (radii, motion, spacing) are shared.
- Rule: components consume **semantic** tokens (`bg-surface`, `text-subtle`) so they theme automatically; raw `ink`/`cream` are for ink-panel compositions (hero, showcase) that intentionally invert.

## 4. Component Inventory

| Component | File | Notes |
|---|---|---|
| Button | `ui/Button.tsx` | Variants (primary/ghost…), sizes (sm…); uppercase display type |
| Alert | `ui/Alert.tsx` | Inline messages (auth errors, notices) |
| Tabs | `ui/Tabs.tsx` | Underline tabs with animated indicator |
| ThemeToggle | `ui/ThemeToggle.tsx` | Sun/moon switch |
| GithubMark | `ui/GithubMark.tsx` | Brand-accurate GitHub glyph |
| ScoreRing | `ui/ScoreRing.tsx` | 0–100 prompt/efficiency score ring |
| EmptyState | `ui/EmptyState.tsx` | Placeholder panels |
| DiffViewer | `code/DiffViewer.tsx` | Unified diff render with add/del tints |
| Header / Sidebar | `layout/` | App chrome; header carries logo lockup + agent status |
| PromptComposer | `agent/PromptComposer.tsx` | Task input + model select + score + run; focus lifts (`border-accent shadow-lift`) |
| AgentStatus / StatusPill | `agent/` | State dot + mono label + sub-status, `aria-live="polite"` |
| ChangesTab / TestsTab / VerificationTab | `run/` | Agent panel tab contents |
| Logo lockup (`Brand`) | `ui/Brand.tsx` | `<img src="/logo.png">` + `CODEFORGE` bold + `AI` in accent, tracking 0.18–0.2em; accepts `onClick` to render as a back button |
| ArchitectureMap | `insights/ArchitectureMap.tsx` | Auto-fitted SVG — the complete architecture always visible at once (viewBox scaling, no zoom/scroll). Directories are labelled boxes, files are dots (accent = entry point), wide sibling levels wrap into bands, clone storage omitted; hover tooltips + repo-overview sidebar |

**Brand lockup (canonical):**

```tsx
<span className="inline-flex items-center gap-2 font-display whitespace-nowrap leading-none">
  <img src="/logo.png" alt="" aria-hidden className="h-[1.7em] w-auto" draggable={false} />
  <span>
    <span className="font-bold tracking-[0.2em]">CODEFORGE</span>{' '}
    <span className="font-medium tracking-[0.2em] text-accent">AI</span>
  </span>
</span>
```

> The legacy `ui/Logo.tsx` was removed in the anvil rebrand (`c84b316`); do not reintroduce it — screens render the lockup above directly.

## 5. Screen Layouts

### 5.1 Landing (`screens/Landing.tsx`)

Header (lockup + nav: Features, How it works, Pricing, Docs, theme toggle) → hero with headline, subcopy, CTAs → feature grid (`#features`) → workflow (`#how`) → **pricing** (`#pricing`: Free $0 / Basic $12 / Pro $29 "Most popular" / Elite $79 — hairline panels, mono eyebrows, sage checks, sign-in CTAs) → footer. Full-bleed ink hero in dark theme; max-w-6xl content width.

### 5.2 Login (`screens/Auth.tsx`) — GitHub-only split card

- Header row: brand lockup (back-to-home button) left, ThemeToggle right.
- Centered **split card** on `bg`:
  - **Left — form:** eyebrow, "Welcome back" display heading, supporting line, primary **Continue with GitHub** button (`GithubMark`), divider, privacy note. All error handling (friendly mapping of Supabase error codes), config-error banner (`supabaseConfigError`), and loading state preserved.
  - **Right — showcase panel:** ink panel with dot-grid texture + soft glows, mini terminal card, branch chip, avatar cluster, `agent/analyze` chip, "repair-verified" badge, ±diff chip; caption **"Ship with an agent, not a chatbot."**
- Password/email login intentionally removed — GitHub is the only path.

### 5.3 Docs (`screens/Docs.tsx`)

In-app product handbook: sticky header (clickable brand → back) + "On this page" sticky TOC sidebar (Getting started · Agent workflow · Tools · Workspace & safety · Prompts · Panels · FAQ) and prose sections in a `max-w-2xl` column. Anchor links use `scroll-mt-24` to clear the sticky header; closing CTA → get started.

### 5.4 Workspace shell (`screens/Workspace.tsx`)

Header (lockup, agent status, theme toggle, menu) + Sidebar view switcher. Views: `repositories` · `files` · `agent` · `changes` · `tests` · `architecture` · `prompt` (Prompt Lab) · `usage` · `efficiency`.

### 5.5 Agent view

Bordered surface panel (`bg-surface`, `shadow-raised`) containing:

1. **Header bar** — Forge tile, mono `forge · {workspaceId}`, live **status pill** right-aligned.
2. **Composer** — PromptComposer with compact variant: task textarea, model select, Prompt Score ring, RUN action.
3. **Tab bar** — ACTIVITY · CHANGES · TESTS · VERIFICATION (underline tabs) + mono event counter (`N events`, `aria-live`).
4. **Tab content** — ACTIVITY: task quote + event timeline (timestamp · state dot · text · detail) + plan list + RESET/VIEW CHANGES actions; CHANGES: file list + DiffViewer; TESTS: pass/fail rows with durations; VERIFICATION: success/failure summary + metrics table + plan.

### 5.6 Status vocabulary (agent states → visuals)

`stateMeta` (`lib/agentState.ts`) maps each `AgentState` to `{label, dot, active}`:

| Dot color | States |
|---|---|
| `bg-green` | READY |
| `bg-sage` | COMPLETED |
| `bg-denim` | ANALYZING, EXPLORING, SEARCHING, READING |
| `bg-burgundy-light` | PLANNING, IMPLEMENTING |
| `bg-burgundy` | MODIFICATION, REPAIR |
| `bg-sage-light` | TESTING, VERIFICATION |
| `bg-blue-gray` | FAILURE_ANALYSIS |
| `bg-rust` | FAILED |

Active states pulse the dot (`animate-pulse-dot`); inactive states render solid.

## 6. Motion & Interaction

- List entrances (timeline, tests): framer-motion, 200–400ms, `--ease-out`, stagger capped (~0.6s max delay), disabled under `prefers-reduced-motion`.
- Tab underline slides between positions; content crossfades (mode="wait").
- Composer focus: border → accent, `shadow-lift`.
- Hover: color transitions only (`duration-fast`); no scale transforms on chrome.
- Every live region that narrates agent progress uses `aria-live="polite"` (status pill, event counter).

## 7. Accessibility Rules

- Semantic landmarks: `header`/`nav`, tablist with `role="tab"` + `aria-selected`, `role="tabpanel"` contents, `aria-label` on icon-only controls.
- Contrast: body text on cream meets AA (`--muted` darkened for this); `--on-accent` fixed light-on-burgundy in both themes.
- Focus states visible (accent border/ring); keyboard path through composer → run → tabs.
- Decorative texture (dot grid, glows) is `aria-hidden`; logos in lockups are `alt=""` beside visible wordmarks.

## 8. Design Conventions (for contributors)

1. All colors/radii/shadows/motion come from tokens — no ad-hoc hex, no arbitrary `rounded-xl`/big shadows.
2. Uppercase mono for micro-labels; display font for headings and buttons; body font for prose.
3. New screens follow the split/panel composition of Auth/Agent: hairline-bordered surfaces, one ink panel for emphasis, generous whitespace, max-w constraints (`max-w-5xl`/`max-w-6xl`).
4. Icons: `lucide-react` only (GitHub glyph via `GithubMark`).
5. Verify changes with `npx tsc -b`, `npx oxlint`, `npm run build` (from `frontend/`); check both themes and `prefers-reduced-motion`.
