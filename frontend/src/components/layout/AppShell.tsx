import type { ReactNode } from 'react'
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
    REPAIR: 'Repair attempt in progress',
    VERIFICATION: 'Checking final result',
    COMPLETED: 'Task completed',
    FAILED: 'Unable to complete task safely',
  }
  if (lastEvent) {
    return `${lastEvent.time}  ${lastEvent.text}`
  }
  return phases[state] || 'Waiting for a task'
}

export function AppShell({ header, sidebar, children, state, lastEvent }: Props) {
  const meta = stateMeta[state]
  return (
    <div className="flex h-screen min-h-0 flex-col bg-bg">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-50 focus:rounded-sm focus:bg-surface focus:px-3 focus:py-2">Skip to content</a>
      {header}
      <div className="flex min-h-0 flex-1 flex-col md:flex-row">
        {sidebar}
        <main id="main" className="scroll-thin min-h-0 flex-1 overflow-y-auto">{children}</main>
      </div>
      <footer className="flex h-10 shrink-0 items-center gap-3 border-t bg-surface px-4 text-xs sm:px-5" aria-label="Agent status">
        <span className="chip !px-2 !py-0.5">Agent</span>
        <span aria-hidden className={`h-1.5 w-1.5 rounded-full ${meta.dot} ${meta.active ? 'animate-pulse-dot' : ''}`} />
        <span className="font-mono font-medium">{meta.label}</span>
        <span className="truncate text-subtle">{getStatusText(state, lastEvent)}</span>
      </footer>
    </div>
  )
}
