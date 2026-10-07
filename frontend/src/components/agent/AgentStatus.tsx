import type { AgentState } from '../../types'
import { stateMeta } from '../../lib/agentState'

export function AgentStatus({ state, tone = 'light' }: { state: AgentState; tone?: 'light' | 'dark' }) {
  const m = stateMeta[state]
  return (
    <span
      className={`inline-flex items-center gap-2 font-display text-[0.6875rem] font-semibold tracking-[0.16em] ${
        tone === 'dark' ? 'text-cream' : 'text-ink'
      }`}
      role="status"
      aria-live="polite"
    >
      <span aria-hidden="true" className={`h-2 w-2 rounded-full ${m.dot} ${m.active ? 'animate-pulse-dot' : ''}`} />
      {m.label}
    </span>
  )
}
