import { useState } from 'react'
import { LogOut, Menu } from 'lucide-react'
import type { AgentState } from '../../types'
import { signOutUser, type User } from '../../lib/supabase'
import { AgentStatus } from '../agent/AgentStatus'
import { ThemeToggle } from '../ui/ThemeToggle'

interface Props {
  state: AgentState
  navOpen: boolean
  onToggleNav: () => void
  theme: 'light' | 'dark'
  onToggleTheme: () => void
  user: User | null
}

export function Header({
  state,
  navOpen,
  onToggleNav,
  theme,
  onToggleTheme,
  user,
}: Props) {
  const [signingOut, setSigningOut] = useState(false)

  const handleSignOut = async () => {
    if (signingOut) return
    setSigningOut(true)
    try {
      await signOutUser()
    } finally {
      setSigningOut(false)
    }
  }

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b bg-surface px-4 sm:gap-4 sm:px-6">
      <button
        type="button"
        onClick={onToggleNav}
        aria-label="Toggle navigation"
        aria-expanded={navOpen}
        aria-controls="primary-nav"
        className="-ml-1.5 rounded-sm p-1.5 text-subtle transition-colors duration-fast hover:text-fg md:hidden"
      >
        <Menu size={18} aria-hidden />
      </button>

      <div className="font-display leading-none">
        <span className="text-[0.875rem] font-bold tracking-[0.15em]">CODEFORGE</span>{' '}
        <span className="text-[0.875rem] font-medium tracking-[0.15em] text-accent">AI</span>
      </div>

      <div className="ml-auto flex items-center gap-3 sm:gap-4">
        <span className="hidden sm:inline-flex">
          <AgentStatus state={state} />
        </span>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        {user && (
          <span className="flex items-center gap-2 border-l pl-3">
            <span
              className="hidden max-w-40 truncate font-mono text-xs text-subtle sm:inline"
              title={user.id}
            >
              {user.user_metadata?.user_name || user.email || 'Signed in'}
            </span>
            <button
              type="button"
              onClick={() => void handleSignOut()}
              disabled={signingOut}
              aria-label="Sign out"
              title="Sign out"
              className="inline-flex h-7 w-7 items-center justify-center rounded-sm text-subtle transition-colors duration-fast hover:bg-raised hover:text-fg disabled:opacity-50"
            >
              <LogOut size={15} aria-hidden />
            </button>
          </span>
        )}
      </div>
    </header>
  )
}
