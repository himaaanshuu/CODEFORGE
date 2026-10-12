import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { Logo } from '../components/ui/Logo'
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
          <Logo className="text-[0.9375rem]" />
        </button>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </header>
      <main className="flex flex-1 items-center justify-center px-6 pb-16">
        <section aria-labelledby="auth-h" className="w-full max-w-sm border bg-surface p-8 shadow-raised">
          <button
            type="button"
            onClick={onBack}
            className="mb-5 inline-flex items-center gap-1.5 text-xs text-subtle transition-colors duration-fast hover:text-fg"
          >
            <ArrowLeft size={13} aria-hidden /> Back
          </button>
          <h1 id="auth-h" className="font-display text-2xl font-bold tracking-tight">
            Sign in
          </h1>
          <p className="mt-1.5 text-sm text-subtle">Continue to your CodeForge workspace</p>

          {!configured && (
            <Alert variant="error" title="Supabase is not configured" className="mt-5 text-xs">
              {supabaseConfigError}
            </Alert>
          )}

          <div className="mt-7">
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

          <p className="mt-2 text-center text-xs text-subtle">
            Sign in with your GitHub account to continue.
          </p>
        </section>
      </main>
    </div>
  )
}
