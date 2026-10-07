import { useCallback, useEffect, useRef, useState } from 'react'
import type { ActivityEvent, AgentRun, AgentState } from '../types'
import { startMockRun } from '../data/mockAgent'

export interface AgentRunState {
  state: AgentState
  events: ActivityEvent[]
  run: AgentRun | null
  running: boolean
  start: (task: string) => void
  reset: () => void
}

export function useAgentRun(): AgentRunState {
  const [state, setState] = useState<AgentState>('READY')
  const [events, setEvents] = useState<ActivityEvent[]>([])
  const [run, setRun] = useState<AgentRun | null>(null)
  const cancel = useRef<(() => void) | null>(null)

  useEffect(() => () => cancel.current?.(), [])

  const start = useCallback((task: string) => {
    cancel.current?.()
    setEvents([]); setRun(null); setState('ANALYZING')
    cancel.current = startMockRun(task, {
      onEvent: e => { setEvents(prev => [...prev, e]); setState(e.state) },
      onComplete: r => { setRun(r); setState('COMPLETED') },
    })
  }, [])

  const reset = useCallback(() => {
    cancel.current?.(); setEvents([]); setRun(null); setState('READY')
  }, [])

  return { state, events, run, running: state !== 'READY' && state !== 'COMPLETED' && state !== 'FAILED', start, reset }
}
