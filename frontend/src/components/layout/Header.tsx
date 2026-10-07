import { Menu, Settings } from 'lucide-react'
import type { AgentState } from '../../types'
import { AgentStatus } from '../agent/AgentStatus'

interface Props { repoPath: string; state: AgentState; onToggleNav: () => void; navOpen: boolean }

export function Header({ repoPath, state, onToggleNav, navOpen }: Props) {
  return (
    <header className="on-ink flex h-14 shrink-0 items-center justify-between gap-4 bg-ink px-4 text-cream sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button" onClick={onToggleNav}
          aria-label="Toggle navigation" aria-expanded={navOpen} aria-controls="primary-nav"
          className="rounded-xs p-1.5 text-cream-muted transition-colors duration-fast hover:text-cream md:hidden"
        >
          <Menu size={18} aria-hidden />
        </button>
        <div className="font-display leading-none">
          <span className="text-[0.9375rem] font-bold tracking-[0.2em]">CODEFORGE</span>{' '}
          <span className="text-[0.9375rem] font-medium tracking-[0.2em] text-burgundy-light">AI</span>
        </div>
      </div>
      <p className="hidden truncate font-mono text-xs text-cream-muted sm:block" aria-label="Current repository">{repoPath}</p>
      <div className="flex items-center gap-5">
        <AgentStatus state={state} tone="dark" />
        <button
          type="button" aria-label="Settings"
          className="inline-flex items-center gap-1.5 rounded-xs font-display text-[0.6875rem] font-semibold tracking-[0.14em] text-cream-muted transition-colors duration-fast hover:text-cream"
        >
          <Settings size={14} aria-hidden /><span className="hidden sm:inline">SETTINGS</span>
        </button>
      </div>
    </header>
  )
}
