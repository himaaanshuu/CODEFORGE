import { useState } from 'react'
import type { ReactNode } from 'react'
import {
  ArrowLeft,
  Check,
  Code2,
  GitBranch,
  GitPullRequest,
  ShieldCheck,
  Terminal,
} from 'lucide-react'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { GithubMark } from '../components/ui/GithubMark'
import { supabaseConfigError, signInWithGitHub } from '../lib/supabase'
import type { Theme } from '../hooks/useTheme'

interface Props {
  theme: Theme
  onToggleTheme: () => void
  onBack: () => void
}

function friendlyAuthError(message: string): string {
  const code = /\(([^)]+)\)/.exec(message)?.[1] ?? ''
  if (code.includes('provider_disabled') || message.includes('provider_disabled')) {
    return 'GitHub sign-in is not enabled for this project yet.'
  }
  if (message.includes('redirect_uri') || message.includes('redirect uri')) {
    return 'GitHub rejected the redirect — add the Supabase callback URL to the OAuth app’s authorized redirect URIs.'
  }
  if (message.includes('signup_disabled')) return 'Sign-ups are disabled for this project.'
  if (message.includes('network') || code.includes('network-request-failed')) {
    return 'Network error. Check your connection.'
  }
  if (message.includes('already')) return 'This account already exists. Try signing in.'
  return message
}

function CollageChip({
  className = '',
  children,
}: {
  className?: string
  children: ReactNode
}) {
  return (
    <div
      aria-hidden="true"
      className={`absolute flex items-center gap-2 rounded-sm border border-cream/15 bg-cream/[0.06] px-3 py-2 text-cream shadow-lift backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  )
}

/** Decorative showcase panel — floating dev-workflow artifacts. Purely visual. */
function Showcase() {
  return (
    <aside aria-hidden="true" className="relative hidden overflow-hidden bg-ink md:block">
      {/* dot grid */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage: 'radial-gradient(rgb(244 240 232 / 0.13) 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
      />
      {/* soft burgundy glow */}
      <div
        className="absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-30 blur-3xl"
        style={{ background: 'rgb(152 64 73 / 0.55)' }}
      />
      <div
        className="absolute -bottom-28 -left-20 h-72 w-72 rounded-full opacity-25 blur-3xl"
        style={{ background: 'rgb(115 119 95 / 0.5)' }}
      />

      {/* mini terminal */}
      <div className="absolute left-[10%] top-[12%] w-[62%] rounded-sm border border-cream/15 bg-ink-soft/90 p-3.5 font-mono text-[11px] leading-relaxed shadow-lift">
        <div className="mb-2 flex items-center gap-1.5 text-cream/50">
          <Terminal size={12} />
          <span>forge — zsh</span>
        </div>
        <p className="text-cream/90">$ forge analyze --repo jaldrishthi</p>
        <p className="text-sage-light">✓ 84 tests passing</p>
        <p className="text-sage-light">✓ patch applied to calculator.py</p>
        <p className="text-cream/90">
          $ <span className="inline-block h-3.5 w-1.5 translate-y-0.5 bg-cream/70" />
        </p>
      </div>

      <CollageChip className="right-[10%] top-[10%]">
        <GitBranch size={13} className="text-denim-light" />
        <span className="font-mono text-[11px]">main</span>
      </CollageChip>

      {/* avatar cluster */}
      <div className="absolute right-[12%] top-[30%] flex -space-x-2.5">
        {['AK', 'JM', '+9'].map((label, i) => (
          <span
            key={label}
            className={`flex h-9 w-9 items-center justify-center rounded-full border-2 border-ink font-display text-[10px] font-semibold ${
              i === 0
                ? 'bg-burgundy text-cream'
                : i === 1
                  ? 'bg-sage text-cream'
                  : 'bg-cream-muted font-mono text-ink'
            }`}
          >
            {label}
          </span>
        ))}
      </div>

      <CollageChip className="left-[12%] top-[52%]">
        <Code2 size={13} className="text-burgundy-light" />
        <span className="font-mono text-[11px]">agent/analyze</span>
      </CollageChip>

      <CollageChip className="right-[14%] top-[55%]">
        <span className="flex h-4 w-4 items-center justify-center rounded-full bg-sage px-1 py-0.5">
          <Check size={11} strokeWidth={3} className="text-cream" />
        </span>
        <span className="text-xs">Repair verified</span>
      </CollageChip>

      <CollageChip className="bottom-[24%] left-[22%]">
        <GitPullRequest size={13} className="text-cream/80" />
        <span className="font-mono text-[11px]">
          <span className="text-sage-light">+128</span>
          <span className="text-cream/40"> / </span>
          <span className="text-burgundy-light">−12</span>
        </span>
      </CollageChip>

      <CollageChip className="bottom-[10%] right-[10%]">
        <ShieldCheck size={13} className="text-sage-light" />
        <span className="text-xs">Private by default</span>
      </CollageChip>

      {/* caption */}
      <p className="absolute bottom-6 left-7 font-display text-sm font-semibold tracking-tight text-cream">
        Ship with an agent,
        <br />
        <span className="text-cream/55">not a chatbot.</span>
      </p>
    </aside>
  )
}

export function Auth({ theme, onToggleTheme, onBack }: Props) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const configured = !supabaseConfigError

  const submit = async () => {
    if (busy) return
    setError(null)
    setBusy(true)
    try {
      await signInWithGitHub()
      // Redirecting to GitHub — useAuth() in App switches the route on return.
    } catch (err) {
      setError(friendlyAuthError(err instanceof Error ? err.message : String(err)))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <header className="flex items-center justify-between px-6 py-5">
        <button type="button" onClick={onBack} aria-label="Back to home" className="rounded-xs">
          <span className="inline-flex items-center gap-2 font-display whitespace-nowrap leading-none text-[0.9375rem]">
            <img src="/logo.png" alt="" aria-hidden className="h-[1.7em] w-auto" draggable={false} />
            <span>
              <span className="font-bold tracking-[0.2em]">CODEFORGE</span>{' '}
              <span className="font-medium tracking-[0.2em] text-accent">AI</span>
            </span>
          </span>
        </button>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </header>
      <main className="flex flex-1 items-center justify-center px-6 pb-16">
        <section
          aria-labelledby="auth-h"
          className="grid w-full max-w-4xl overflow-hidden border bg-surface shadow-raised md:grid-cols-[1fr_1.1fr]"
        >
          {/* form side */}
          <div className="p-8 sm:p-10">
            <button
              type="button"
              onClick={onBack}
              className="mb-6 inline-flex items-center gap-1.5 text-xs text-subtle transition-colors duration-fast hover:text-fg"
            >
              <ArrowLeft size={13} aria-hidden /> Back
            </button>
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-subtle">
              CodeForge AI
            </p>
            <h1 id="auth-h" className="mt-2 font-display text-3xl font-bold tracking-tight">
              Welcome back
            </h1>
            <p className="mt-2 text-sm text-subtle">
              Sign in to pick up your repositories and keep shipping.
            </p>

            {!configured && (
              <Alert variant="error" title="Supabase is not configured" className="mt-5 text-xs">
                {supabaseConfigError}
              </Alert>
            )}

            <div className="mt-8">
              <Button full disabled={!configured || busy} onClick={() => void submit()}>
                <GithubMark size={15} />
                <span className="uppercase">{busy ? 'Redirecting…' : 'Continue with GitHub'}</span>
              </Button>
            </div>

            {error && (
              <Alert variant="error" title="Sign-in failed" className="mt-4 text-xs">
                {error}
              </Alert>
            )}

            <div className="mt-6 flex items-center gap-3 text-[11px] text-subtle">
              <span className="h-px flex-1 bg-border" aria-hidden="true" />
              <span className="uppercase tracking-[0.12em]">GitHub only</span>
              <span className="h-px flex-1 bg-border" aria-hidden="true" />
            </div>
            <p className="mt-4 text-center text-xs leading-relaxed text-subtle">
              We use GitHub to read the repos you connect — nothing else. First
              sign-in creates your workspace automatically.
            </p>
          </div>

          {/* showcase side */}
          <Showcase />
        </section>
      </main>
    </div>
  )
}
