import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import type { ActivityEvent } from '../../types'
import { stateMeta } from '../../lib/agentState'

interface Props { events: ActivityEvent[]; running: boolean; compact?: boolean }

export function AgentActivity({ events, running, compact }: Props) {
  const reduce = useReducedMotion()
  return (
    <section aria-label="Agent activity" className={compact ? '' : 'mx-auto w-full max-w-3xl px-6 py-10'}>
      <h3 className="eyebrow">Agent activity</h3>
      {events.length === 0 ? (
        <p className="mt-4 text-sm text-subtle">No activity yet. Run a task to see what the agent does.</p>
      ) : (
        <ol className="panel mt-4 overflow-hidden p-0">
          <AnimatePresence initial={false}>
            {events.map((e, i) => {
              const last = i === events.length - 1
              const active = running && last
              const failed = e.status === 'failed'
              const dot = failed ? 'bg-rust' : stateMeta[e.state]?.dot ?? 'bg-sage'
              return (
                <motion.li
                  key={e.id}
                  initial={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
                  className="flex items-baseline gap-4 border-b border-[color:var(--line)] px-4 py-3 last:border-b-0"
                >
                  <time className="w-16 shrink-0 font-mono text-xs tabular-nums text-muted">{e.time}</time>
                  <span aria-hidden="true" className={`h-1.5 w-1.5 shrink-0 translate-y-[-1px] rounded-full ${dot} ${active ? 'animate-pulse-dot' : ''}`} />
                  <span className="min-w-0 flex-1 text-sm">
                    <span className={failed ? 'text-rust' : ''}>{e.text}</span>
                    {e.detail && (
                      <span className="mt-0.5 block truncate font-mono text-[0.6875rem] text-subtle" title={e.detail}>
                        {e.detail}
                      </span>
                    )}
                  </span>
                </motion.li>
              )
            })}
          </AnimatePresence>
        </ol>
      )}
    </section>
  )
}
