import { useCallback, useRef, useState } from 'react'
import type { ActivityEvent, AgentRunView, AgentState } from '../types'
import { startAgentTask } from '../lib/agentClient'

export interface AgentController {
  state: AgentState
  events: ActivityEvent[]
  run: AgentRunView | null
  running: boolean
  start: (task: string, workspaceId: string, model?: string) => void
  reset: () => void
}

export function useAgentRun(): AgentController {
  const [state, setState] = useState<AgentState>('READY')
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [run, setRun] = useState<AgentRunView | null>(null)
  // Monotonic id so a stale run's callbacks never overwrite a newer run.
  const runId = useRef(0)

  const start = useCallback((task: string, workspaceId: string, model?: string) => {
    const id = ++runId.current
    setEvents([]); setRun(null); setState('ANALYZING')
    startAgentTask(
      task,
      workspaceId,
      (event) => {
        if (runId.current !== id) return
        setEvents(prev => [...prev, event])
        setState(event.state)
      },
      (result) => {
        if (runId.current !== id) return
        setRun(result)
        setState(result.success ? 'COMPLETED' : 'FAILED')
      },
      model,
    )
  }, [])

  const reset = useCallback(() => {
    runId.current += 1
    setEvents([]); setRun(null); setState('READY')
  }, [])

  const running =
    state !== 'READY' && state !== 'COMPLETED' && state !== 'FAILED'

  return { state, events, run, running, start, reset }
}
