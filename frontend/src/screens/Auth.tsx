import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import {
  ArrowLeft,
  Check,
  Code2,
  GitBranch,
  GitPullRequest,
  ShieldCheck,
  Terminal,
} from 'lucide-react'
import { Brand } from '../components/ui/Brand'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { Alert } from '../components/ui/Alert'
import { Button } from '../components/ui/Button'
import { GithubMark } from '../components/ui/GithubMark'
import { supabaseConfigError, signInWithGitHub } from '../lib/supabase'
import type { Theme } from '../hooks/useTheme'

export type AuthMode = 'signin' | 'signup'

interface Props {
  theme: Theme
  onToggleTheme: () => void
  onBack: () => void
  mode: AuthMode
}

const COPY: Record<AuthMode, { chip: string; title: string; sub: string; cta: string; alt: string; altTo: AuthMode }> = {
  signin: {
    chip: 'GitHub only',
    title: 'Welcome back',
    sub: 'Sign in to pick up your repositories and keep shipping. First sign-in creates your workspace automatically.',
    cta: 'Continue with GitHub',
    alt: 'New here? Create an account',
    altTo: 'signup',
  },
  signup: {
    chip: 'Free to start',
    title: 'Create your account',
    sub: 'Sign up with GitHub — your workspace is created on the spot. No credit card, no setup, cancel anytime.',
    cta: 'Sign up with GitHub',
    alt: 'Already have an account? Sign in',
    altTo: 'signin',
  },
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

/* ------------------------------------------------------------------ *
 * Animated showcase (right panel)
 * ------------------------------------------------------------------ */

const TERMINAL_CMD = '$ forge run "add rate limiting to /login"'
const TERMINAL_LINES: { text: string; cls: string }[] = [
  { text: '→ exploring app/auth · 14 files', cls: 'text-denim-light' },
  { text: '→ plan: protect routes, keep login shape', cls: 'text-cream/70' },
  { text: '✓ 84 tests passing', cls: 'text-sage-light' },
  { text: '✓ repair verified · patch applied', cls: 'text-sage-light' },
]

function TerminalDemo({ reduce }: { reduce: boolean }) {
  const [typedRaw, setTyped] = useState(0)
  const [shownRaw, setShown] = useState(0)
  const typed = reduce ? TERMINAL_CMD.length : typedRaw
  const shown = reduce ? TERMINAL_LINES.length : shownRaw

  useEffect(() => {
    if (reduce) return
    let alive = true
    let timer = 0
    const wait = (ms: number) => new Promise<void>((res) => { timer = window.setTimeout(res, ms) })
    const run = async () => {
      while (alive) {
        setTyped(0)
        setShown(0)
        for (let i = 1; i <= TERMINAL_CMD.length && alive; i++) {
          setTyped(i)
          await wait(34)
        }
        await wait(380)
        for (let i = 1; i <= TERMINAL_LINES.length && alive; i++) {
          setShown(i)
          await wait(560)
        }
        await wait(2600)
      }
    }
    void run()
    return () => {
      alive = false
      window.clearTimeout(timer)
    }
  }, [reduce])

  const progress = shown / TERMINAL_LINES.length

  return (
    <div className="rounded-md border border-cream/15 bg-ink-soft/90 p-4 font-mono text-[11px] leading-relaxed shadow-lift backdrop-blur-sm">
      <div className="mb-2 flex items-center gap-1.5 text-cream/50">
        <Terminal size={12} />
        <span>forge — zsh</span>
      </div>
      <p className="text-cream/90">
        {TERMINAL_CMD.slice(0, typed)}
        {typed < TERMINAL_CMD.length && (
          <span className="inline-block h-3.5 w-1.5 translate-y-0.5 bg-burgundy-light caret-burgundy-light" />
        )}
      </p>
      {TERMINAL_LINES.slice(0, shown).map((l) => (
        <p key={l.text} className={`${l.cls} animate-fade-in`}>{l.text}</p>
      ))}
      <div className="mt-3 h-0.5 overflow-hidden rounded-full bg-cream/10">
        <div
          className="h-full rounded-full bg-sage transition-[width] duration-500 ease-out"
          style={{ width: `${Math.round(progress * 100)}%` }}
        />
      </div>
    </div>
  )
}

function Float({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const reduce = useReducedMotion()
  if (reduce) return <>{children}</>
  return (
    <motion.div
      animate={{ y: [0, -7, 0] }}
      transition={{ duration: 3.4 + delay, repeat: Infinity, ease: 'easeInOut', delay }}
    >
      {children}
    </motion.div>
  )
}

function CollageChip({ className = '', children }: { className?: string; children: ReactNode }) {
  return (
    <div
      aria-hidden="true"
      className={`absolute flex items-center gap-2 rounded-sm border border-cream/15 bg-cream/[0.08] px-3 py-2 text-cream shadow-lift backdrop-blur-sm ${className}`}
    >
      {children}
    </div>
  )
}

function Showcase({ reduce }: { reduce: boolean }) {
  const drift = (i: number) =>
    reduce
      ? {}
      : {
          animate: { x: [0, 22 - i * 8, 0], y: [0, -14 + i * 6, 0] },
          transition: { duration: 15 + i * 3, repeat: Infinity, ease: 'easeInOut' as const },
        }

  const enter = (i: number) =>
    reduce
      ? {}
      : {
          initial: { opacity: 0, y: 14 },
          animate: { opacity: 1, y: 0 },
          transition: { delay: 0.25 + i * 0.09, duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
        }

  return (
    <aside aria-hidden="true" className="relative hidden overflow-hidden bg-ink md:block">
      <div
        className="absolute inset-0 opacity-50"
        style={{
          backgroundImage: 'radial-gradient(rgb(244 240 232 / 0.13) 1px, transparent 1px)',
          backgroundSize: '22px 22px',
        }}
      />
      <motion.div
        className="absolute -right-24 -top-24 h-72 w-72 rounded-full opacity-30 blur-3xl"
        style={{ background: 'rgb(152 64 73 / 0.55)' }}
        {...drift(0)}
      />
      <motion.div
        className="absolute -bottom-28 -left-20 h-72 w-72 rounded-full opacity-25 blur-3xl"
        style={{ background: 'rgb(115 119 95 / 0.5)' }}
        {...drift(1)}
      />
      <motion.div
        className="absolute left-1/3 top-1/3 h-56 w-56 rounded-full opacity-15 blur-3xl"
        style={{ background: 'rgb(104 116 122 / 0.6)' }}
        {...drift(2)}
      />

      <motion.div className="absolute left-[10%] top-[14%] w-[62%]" {...enter(0)}>
        <TerminalDemo reduce={reduce} />
      </motion.div>

      <motion.div className="absolute right-[10%] top-[10%]" {...enter(1)}>
        <Float delay={0.2}>
          <CollageChip className="relative">
            <GitBranch size={13} className="text-denim-light" />
            <span className="font-mono text-[11px]">main</span>
          </CollageChip>
        </Float>
      </motion.div>

      <motion.div
        className="absolute right-[12%] top-[32%] flex -space-x-2.5"
        {...enter(2)}
      >
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
      </motion.div>

      <motion.div className="absolute left-[12%] top-[54%]" {...enter(3)}>
        <Float delay={0.6}>
          <CollageChip className="relative">
            <Code2 size={13} className="text-burgundy-light" />
            <span className="font-mono text-[11px]">agent/analyze</span>
          </CollageChip>
        </Float>
      </motion.div>

      <motion.div className="absolute right-[14%] top-[57%]" {...enter(4)}>
        <Float delay={0.9}>
          <CollageChip className="relative">
            <span className="flex h-4 w-4 items-center justify-center rounded-full bg-sage px-1 py-0.5">
              <Check size={11} strokeWidth={3} className="text-cream" />
            </span>
            <span className="text-xs">Repair verified</span>
          </CollageChip>
        </Float>
      </motion.div>

      <motion.div className="absolute bottom-[24%] left-[22%]" {...enter(5)}>
        <Float delay={1.2}>
          <CollageChip className="relative">
            <GitPullRequest size={13} className="text-cream/80" />
            <span className="font-mono text-[11px]">
              <span className="text-sage-light">+128</span>
              <span className="text-cream/40"> / </span>
              <span className="text-burgundy-light">−12</span>
            </span>
          </CollageChip>
        </Float>
      </motion.div>

      <motion.div className="absolute bottom-[12%] right-[10%]" {...enter(6)}>
        <Float delay={1.5}>
          <CollageChip className="relative">
            <ShieldCheck size={13} className="text-sage-light" />
            <span className="text-xs">Private by default</span>
          </CollageChip>
        </Float>
      </motion.div>

      <motion.p
        className="absolute bottom-8 left-8 font-display text-lg font-semibold tracking-tight text-cream"
        {...enter(7)}
      >
        Ship with an agent,
        <br />
        <span className="text-cream/55">not a chatbot.</span>
      </motion.p>
    </aside>
  )
}

/* ------------------------------------------------------------------ *
 * Screen
 * ------------------------------------------------------------------ */

export function Auth({ theme, onToggleTheme, onBack, mode: modeProp }: Props) {
  const reduce = useReducedMotion() ?? false
  const [mode, setMode] = useState<AuthMode>(modeProp)
  const [lastProp, setLastProp] = useState<AuthMode>(modeProp)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Sync internal toggle state when the prop changes (adjust-during-render).
  if (modeProp !== lastProp) {
    setLastProp(modeProp)
    setMode(modeProp)
    setError(null)
  }

  const configured = !supabaseConfigError
  const copy = COPY[mode]

  const switchMode = (m: AuthMode) => {
    if (m === mode) return
    setMode(m)
    setError(null)
  }

  const submit = async () => {
    if (busy) return
    setError(null)
    setBusy(true)
    try {
      await signInWithGitHub()
    } catch (err) {
      setError(friendlyAuthError(err instanceof Error ? err.message : String(err)))
    } finally {
      setBusy(false)
    }
  }

  const stagger = (i: number) =>
    reduce
      ? {}
      : {
          initial: { opacity: 0, y: 12 },
          animate: { opacity: 1, y: 0 },
          transition: { delay: 0.05 + i * 0.07, duration: 0.45, ease: [0.22, 1, 0.36, 1] as const },
        }

  return (
    <div className="grid min-h-screen bg-bg md:grid-cols-[minmax(0,26rem)_1fr] lg:grid-cols-[minmax(0,32rem)_1fr]">
      <div className="relative flex min-h-screen flex-col overflow-hidden px-6 py-5 sm:px-10">
        {/* slow drifting aurora */}
        <motion.div
          aria-hidden
          className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-burgundy opacity-[0.14] blur-3xl"
          animate={reduce ? undefined : { x: [0, 26, 0], y: [0, 20, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
        <motion.div
          aria-hidden
          className="pointer-events-none absolute -bottom-40 -right-24 h-80 w-80 rounded-full bg-sage opacity-[0.12] blur-3xl"
          animate={reduce ? undefined : { x: [0, -18, 0], y: [0, -16, 0] }}
          transition={{ duration: 21, repeat: Infinity, ease: 'easeInOut' }}
        />

        <header className="relative flex items-center justify-between">
          <button type="button" onClick={onBack} aria-label="Back to home" className="rounded-xs">
            <Brand />
          </button>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </header>

        <main className="relative flex flex-1 flex-col justify-center py-12">
          <motion.button
            {...stagger(0)}
            type="button"
            onClick={onBack}
            className="mb-7 inline-flex items-center gap-1.5 self-start text-xs text-subtle transition-colors duration-fast hover:text-fg"
          >
            <ArrowLeft size={13} aria-hidden /> Back
          </motion.button>

          {/* segmented sign in / sign up */}
          <motion.div
            {...stagger(1)}
            role="tablist"
            aria-label="Authentication mode"
            className="grid max-w-sm grid-cols-2 gap-1 rounded-sm border bg-surface p-1"
          >
            {(['signin', 'signup'] as const).map((m) => {
              const on = m === mode
              return (
                <button
                  key={m}
                  role="tab"
                  type="button"
                  aria-selected={on}
                  onClick={() => switchMode(m)}
                  className="relative rounded-xs px-3 py-2 font-display text-xs font-semibold tracking-[0.1em]"
                >
                  {on && (
                    <motion.span
                      layoutId="auth-seg"
                      className="absolute inset-0 rounded-xs bg-burgundy"
                      transition={{ type: 'spring', stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span className={`relative z-10 ${on ? 'text-on-accent' : 'text-subtle hover:text-fg'}`}>
                    {m === 'signin' ? 'SIGN IN' : 'SIGN UP'}
                  </span>
                </button>
              )
            })}
          </motion.div>

          {/* mode-coupled copy */}
          <div className="mt-7 max-w-sm min-h-[10.5rem]">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={mode}
                initial={reduce ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={reduce ? undefined : { opacity: 0, y: -8 }}
                transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
              >
                <p className="chip w-fit">{copy.chip}</p>
                <h1 className="mt-4 font-display text-4xl font-bold tracking-tight">{copy.title}</h1>
                <p className="mt-3 text-sm leading-relaxed text-subtle">{copy.sub}</p>
              </motion.div>
            </AnimatePresence>
          </div>

          {!configured && (
            <motion.div {...stagger(3)}>
              <Alert variant="error" title="Supabase is not configured" className="max-w-sm text-xs">
                {supabaseConfigError}
              </Alert>
            </motion.div>
          )}

          <motion.div {...stagger(4)} className="mt-6 max-w-sm">
            <Button full disabled={!configured || busy} onClick={() => void submit()}>
              <GithubMark size={15} />
              <span>{busy ? 'Redirecting…' : copy.cta}</span>
            </Button>
          </motion.div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={reduce ? false : { opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="max-w-sm"
              >
                <Alert variant="error" title="Sign-in failed" className="mt-4 text-xs">
                  {error}
                </Alert>
              </motion.div>
            )}
          </AnimatePresence>

          <motion.button
            {...stagger(5)}
            type="button"
            onClick={() => switchMode(copy.altTo)}
            className="mt-5 max-w-sm self-start text-xs text-subtle underline-offset-4 transition-colors duration-fast hover:text-fg hover:underline"
          >
            {copy.alt}
          </motion.button>

          <motion.p {...stagger(6)} className="mt-7 max-w-sm text-xs leading-relaxed text-subtle">
            {mode === 'signin'
              ? 'We use GitHub to read the repos you connect — nothing else.'
              : 'By continuing, you agree to use CodeForge responsibly on the repos you connect.'}
          </motion.p>
        </main>
      </div>
      <Showcase reduce={reduce} />
    </div>
  )
}
