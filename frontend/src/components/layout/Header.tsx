import { useState } from 'react'
import { LogOut, Menu } from 'lucide-react'
import type { AgentState } from '../../types'
import { signOutUser, type User } from '../../lib/supabase'
import { AgentStatus } from '../agent/AgentStatus'
import { Brand } from '../ui/Brand'
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

  const handle = user?.user_metadata?.user_name || user?.email || 'Signed in'

  return (
    <header className="flex h-16 shrink-0 items-center gap-3 border-b bg-surface/90 px-4 backdrop-blur-sm sm:gap-4 sm:px-5">
      <button
        type="button"
        onClick={onToggleNav}
        aria-label="Toggle navigation"
        aria-expanded={navOpen}
        aria-controls="primary-nav"
        className="-ml-1 rounded-sm p-1.5 text-subtle transition-colors duration-fast hover:bg-raised hover:text-fg md:hidden"
      >
        <Menu size={18} aria-hidden />
      </button>

      <Brand size="sm" />

      <div className="ml-auto flex items-center gap-2.5 sm:gap-3">
        <span className="hidden rounded-full border bg-raised px-3 py-1.5 sm:inline-flex">
          <AgentStatus state={state} />
        </span>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        {user && (
          <span className="flex items-center gap-2 rounded-full border bg-raised py-1 pl-2.5 pr-1">
            <span
              className="flex h-6 w-6 items-center justify-center rounded-full bg-burgundy font-display text-[10px] font-bold text-on-accent"
              aria-hidden
            >
              {String(handle).slice(0, 1).toUpperCase()}
            </span>
            <span
              className="hidden max-w-36 truncate font-mono text-[11px] text-subtle sm:inline"
              title={user.id}
            >
              {handle}
            </span>
            <button
              type="button"
              onClick={() => void handleSignOut()}
              disabled={signingOut}
              aria-label="Sign out"
              title="Sign out"
              className="inline-flex h-7 w-7 items-center justify-center rounded-full text-subtle transition-colors duration-fast hover:bg-surface hover:text-fg disabled:opacity-50"
            >
              <LogOut size={14} aria-hidden />
            </button>
          </span>
        )}
      </div>
    </header>
  )
}
