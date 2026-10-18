import { ArrowLeft } from 'lucide-react'
import { Brand } from '../components/ui/Brand'
import { Button } from '../components/ui/Button'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import type { Theme } from '../hooks/useTheme'

interface Props {
  theme: Theme
  onToggleTheme: () => void
  onBack: () => void
  onStart: () => void
}

const sections = [
  { id: 'start', label: 'Getting started' },
  { id: 'workflow', label: 'The agent workflow' },
  { id: 'tools', label: 'Agent tools' },
  { id: 'safety', label: 'Workspace & safety' },
  { id: 'prompts', label: 'Writing good prompts' },
  { id: 'panels', label: 'Reading the panels' },
  { id: 'faq', label: 'FAQ' },
]

const tools = [
  ['list_files', 'Lists files and folders inside the workspace, confined to the repository root.'],
  ['read_file', 'Reads a file with line limits and size caps so context stays cheap.'],
  ['search_code', 'Regex/text search across the workspace to locate symbols and routes.'],
  ['apply_patch', 'Applies real unified diffs, multi-file, atomically — a failed patch never leaves a half-written file.'],
  ['inspect_diff', 'Shows the live git diff, status, and per-file change counts for what the agent has done.'],
  ['run_tests', 'Runs your allow-listed test suite in a sandbox (60s timeout, output capped, sanitized environment).'],
]

const faqs = [
  ['Does the agent push or open PRs?', 'Not yet. Branch and commit automation are in development; pull-request creation is planned. You stay in control of what leaves the workspace.'],
  ['What happens when tests fail?', 'The agent enters the repair loop (up to 5 attempts): it diagnoses the failure, applies a fix, and re-runs tests. Every step is visible in the ACTIVITY timeline.'],
  ['Can it touch files outside my repo?', 'No. Every path resolves inside a chroot-style workspace boundary; traversal attempts are rejected, and unknown commands are refused by the sandbox.'],
  ['Which GitHub account data do you store?', 'Only what OAuth provides for sign-in and repo listing. Repos are cloned into an isolated workspace; run history is stored per user.'],
  ['Can I cancel a plan anytime?', 'Yes — plans are monthly and cancellable at any time; your run history remains available until the end of the paid period.'],
]

export function Docs({ theme, onToggleTheme, onBack, onStart }: Props) {
  return (
    <div className="min-h-screen bg-bg">
      <header className="sticky top-0 z-20 border-b bg-bg/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-3.5">
          <Brand onClick={onBack} ariaLabel="Back to home" />
          <nav aria-label="Primary" className="hidden items-center gap-7 text-sm text-subtle md:flex">
            <button type="button" onClick={onBack} className="transition-colors duration-fast hover:text-fg">Home</button>
            <span className="text-fg">Docs</span>
            <button type="button" onClick={onBack} className="transition-colors duration-fast hover:text-fg">Pricing</button>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <Button size="sm" onClick={onStart}>Get started</Button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-12 px-6 py-12 lg:grid-cols-[14rem_1fr]">
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <button
            type="button"
            onClick={onBack}
            className="mb-6 inline-flex items-center gap-1.5 text-xs text-subtle transition-colors duration-fast hover:text-fg"
          >
            <ArrowLeft size={13} aria-hidden /> Back
          </button>
          <p className="eyebrow">On this page</p>
          <nav aria-label="Docs sections" className="mt-3 space-y-1.5">
            {sections.map(s => (
              <a
                key={s.id}
                href={`#${s.id}`}
                className="block text-sm text-subtle transition-colors duration-fast hover:text-fg"
              >
                {s.label}
              </a>
            ))}
          </nav>
        </aside>

        <div className="min-w-0 max-w-2xl">
          <p className="chip">Documentation</p>
          <h1 className="mt-5 font-display text-4xl font-bold tracking-tight">CodeForge AI handbook</h1>
          <p className="mt-4 text-sm leading-relaxed text-subtle">
            How the autonomous agent works, what it is allowed to do, and how to get verified code out of a single prompt.
          </p>

          <section id="start" aria-labelledby="start-h" className="mt-14 scroll-mt-24">
            <h2 id="start-h" className="font-display text-2xl font-bold tracking-tight">Getting started</h2>
            <ol className="mt-4 space-y-3">
              {[
                ['Sign in with GitHub', 'The only sign-in method. First sign-in creates your workspace automatically.'],
                ['Connect a repository', 'Clone any GitHub repository into an isolated workspace with one click.'],
                ['Describe the task', 'Write what you want changed — a bug fix, a feature, a refactor. Prompt Lab scores and improves it.'],
                ['Run the agent', 'Watch the ACTIVITY timeline, review the CHANGES diff, confirm TESTS, and read the VERIFICATION summary.'],
              ].map(([title, body], i) => (
                <li key={title} className="flex gap-4">
                  <span className="font-mono text-xs text-accent">{String(i + 1).padStart(2, '0')}</span>
                  <div>
                    <p className="font-display text-sm font-semibold">{title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-subtle">{body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          <section id="workflow" aria-labelledby="workflow-h" className="mt-14 scroll-mt-24">
            <h2 id="workflow-h" className="font-display text-2xl font-bold tracking-tight">The agent workflow</h2>
            <p className="mt-3 text-sm leading-relaxed text-subtle">
              Every run follows the same closed loop — this is what separates CodeForge from a chatbot:
            </p>
            <ol className="mt-4 grid gap-2 sm:grid-cols-2">
              {[
                ['Understand', 'Reads your task and the codebase structure.'],
                ['Explore', 'Finds the files that matter via search and reads.'],
                ['Plan', 'Produces an ordered plan you can see in the UI.'],
                ['Build', 'Applies edits as atomic unified-diff patches.'],
                ['Test', 'Runs your suite in a sandbox.'],
                ['Repair', 'Diagnoses failures and fixes them (up to 5 attempts).'],
                ['Verify', 'Re-runs the full suite; success is only reported when everything passes.'],
              ].map(([label, note]) => (
                <li key={label} className="rounded-md border bg-surface p-3.5">
                  <p className="font-display text-sm font-semibold">{label}</p>
                  <p className="mt-1 text-xs leading-snug text-subtle">{note}</p>
                </li>
              ))}
            </ol>
          </section>

          <section id="tools" aria-labelledby="tools-h" className="mt-14 scroll-mt-24">
            <h2 id="tools-h" className="font-display text-2xl font-bold tracking-tight">Agent tools</h2>
            <p className="mt-3 text-sm leading-relaxed text-subtle">
              The agent has no arbitrary shell access — it can only act through these controlled tools:
            </p>
            <dl className="mt-4 border-t">
              {tools.map(([name, desc]) => (
                <div key={name} className="border-b py-3">
                  <dt className="font-mono text-sm font-semibold text-accent">{name}</dt>
                  <dd className="mt-1 text-sm leading-relaxed text-subtle">{desc}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section id="safety" aria-labelledby="safety-h" className="mt-14 scroll-mt-24">
            <h2 id="safety-h" className="font-display text-2xl font-bold tracking-tight">Workspace &amp; safety</h2>
            <ul className="mt-4 space-y-3">
              {[
                ['Chroot boundary', 'Every filesystem operation resolves inside the workspace root; path traversal is rejected.'],
                ['Atomic patches', 'A patch either applies fully or not at all — files are never left half-written.'],
                ['Sandboxed tests', 'Only allow-listed test commands run, with a 60s timeout, sanitized environment, and capped output.'],
                ['Honest failure', 'If the loop exhausts its budget, the run reports FAILED with diagnostics — never a fake success.'],
              ].map(([title, body]) => (
                <li key={title}>
                  <p className="font-display text-sm font-semibold">{title}</p>
                  <p className="mt-1 text-sm leading-relaxed text-subtle">{body}</p>
                </li>
              ))}
            </ul>
          </section>

          <section id="prompts" aria-labelledby="prompts-h" className="mt-14 scroll-mt-24">
            <h2 id="prompts-h" className="font-display text-2xl font-bold tracking-tight">Writing good prompts</h2>
            <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-relaxed text-subtle">
              <li>Name the outcome, not the implementation: “Add rate limiting to /login” beats “edit middleware”.</li>
              <li>Mention constraints: keep the public API shape, don’t touch migrations, target Python 3.11.</li>
              <li>Reference paths or symbols when you know them — the agent will verify before editing.</li>
              <li>Let Prompt Lab help: the score highlights missing scope, test expectations, and acceptance criteria.</li>
            </ul>
          </section>

          <section id="panels" aria-labelledby="panels-h" className="mt-14 scroll-mt-24">
            <h2 id="panels-h" className="font-display text-2xl font-bold tracking-tight">Reading the panels</h2>
            <dl className="mt-4 space-y-3">
              {[
                ['ACTIVITY', 'Live timeline of every tool call, observation, and plan step.'],
                ['CHANGES', 'File-by-file unified diffs of what the agent actually wrote.'],
                ['TESTS', 'Pass/fail rows with durations from the sandboxed suite runs.'],
                ['VERIFICATION', 'Final summary: outcome, metrics, model, and the plan that was executed.'],
              ].map(([name, desc]) => (
                <div key={name}>
                  <dt className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-accent">{name}</dt>
                  <dd className="mt-1 text-sm leading-relaxed text-subtle">{desc}</dd>
                </div>
              ))}
            </dl>
          </section>

          <section id="faq" aria-labelledby="faq-h" className="mt-14 scroll-mt-24">
            <h2 id="faq-h" className="font-display text-2xl font-bold tracking-tight">FAQ</h2>
            <dl className="mt-4 border-t">
              {faqs.map(([q, a]) => (
                <div key={q} className="border-b py-4">
                  <dt className="font-display text-sm font-semibold">{q}</dt>
                  <dd className="mt-1.5 text-sm leading-relaxed text-subtle">{a}</dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="mt-14 border-t pt-8">
            <p className="text-sm text-subtle">Ready to let the agent ship something real?</p>
            <div className="mt-4">
              <Button onClick={onStart}>Get started free</Button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
