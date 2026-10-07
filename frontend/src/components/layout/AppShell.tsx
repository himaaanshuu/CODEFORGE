import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import type { AgentState, ActivityEvent } from '../../types'
import { stateMeta } from '../../lib/agentState'

interface Props {
  header: ReactNode
  sidebar: ReactNode
  children: ReactNode
  state: AgentState
  lastEvent?: ActivityEvent
}

function getStatusText(state: AgentState, lastEvent?: ActivityEvent): string {
const phases: Record<AgentState, string> = {
    READY: 'Waiting for a task',
    ANALYZING: 'Exploring repository',
    EXPLORING: 'Exploring repository',
    SEARCHING: 'Searching source code',
    READING: 'Reading file',
    PLANNING: 'Building implementation plan',
    IMPLEMENTING: 'Implementing changes',
    MODIFICATION: 'Applying code changes',
    TESTING: 'Running repository tests',
    FAILURE_ANALYSIS: 'Diagnosing test failure',
    REPAIR: 'Repair attempt 1 of 5',
    VERIFICATION: 'Checking final result',
    COMPLETED: '31 tests passed',
    FAILED: 'Unable to complete task safely',
}
  if (lastEvent) {
    return `${lastEvent.time}  ${lastEvent.text}`
  }
  return phases[state] || 'Waiting for a task'
}

export function AppShell({ header, sidebar, children, state, lastEvent }: Props) {
  const reduce = useReducedMotion()
  const meta = stateMeta[state]
  return (
    <motion.div
      className="flex h-screen min-h-0 flex-col"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: reduce ? 0.1 : 0.5 }}
    >
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:bg-cream focus:px-3 focus:py-2">Skip to content</a>
      {header}
      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        {sidebar}
        <main id="main" className="scroll-thin min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
      <footer className="flex h-9 shrink-0 items-center gap-3 border-t border-[color:var(--border)] bg-cream-deep px-4 text-xs sm:px-6" aria-label="Agent status">
        <span className="eyebrow !text-ink">Agent</span>
        <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${meta.dot} ${meta.active ? 'animate-pulse-dot' : ''}`} />
        <span className="font-mono">{meta.label}</span>
        <span className="truncate text-muted">{getStatusText(state, lastEvent)}</span>
      </footer>
    </motion.div>
  )
}
