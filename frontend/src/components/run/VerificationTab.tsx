import { motion, useReducedMotion } from 'framer-motion'
import { ShieldAlert, ShieldCheck } from 'lucide-react'
import type { AgentRunView } from '../../types'
import { fmtInt } from '../../lib/format'

export function VerificationTab({ run }: { run: AgentRunView | null }) {
  const reduce = useReducedMotion()
  if (!run) {
    return <p className="py-6 text-sm text-subtle">Nothing to verify yet. A summary appears when the agent completes a run.</p>
  }

  const m = run.metrics
  const rows: [string, string, boolean?][] = [
    ['Status', run.success ? 'Completed' : `Failed (${run.status})`, run.success],
    ['Files changed', String(m.filesChanged)],
    ['Tests', run.tests ? `${run.tests.tests.filter(t => t.passed).length} passed` : 'N/A'],
    ['Iterations', `${m.iterations} / ${m.maxIterations}`],
    ['Repair attempts', String(m.repairAttempts)],
    ['Tokens used', m.tokensUsed > 0 ? fmtInt(m.tokensUsed) : 'N/A'],
    ['Wall time', m.durationSeconds > 0 ? `${m.durationSeconds}s` : 'N/A'],
    ['Model', m.model || 'N/A'],
  ]

  return (
    <motion.section
      aria-label="Run summary" className="max-w-xl py-1"
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className={`panel flex items-center gap-4 p-5 ${run.success ? 'border-ok/40' : 'border-bad/40'}`}>
        {run.success
          ? <ShieldCheck size={28} className="text-ok" aria-hidden />
          : <ShieldAlert size={28} className="text-bad" aria-hidden />}
        <div>
          <h3 className="font-display text-2xl font-bold tracking-tight">
            {run.success ? 'Completed' : 'Failed'}
          </h3>
          <p className="text-sm text-subtle">{run.message}</p>
        </div>
      </div>

      <dl className="panel mt-5 overflow-hidden p-0">
        {rows.map(([k, v, ok]) => (
          <div key={k} className="flex items-baseline justify-between border-b border-[color:var(--line)] px-4 py-2.5 text-sm last:border-b-0">
            <dt className="text-subtle">{k}</dt>
            <dd className={`font-mono tabular-nums ${ok ? 'text-ok' : ''}`}>{v}</dd>
          </div>
        ))}
      </dl>

      {run.plan.length > 0 && (
        <>
          <p className="eyebrow mt-7">Plan produced</p>
          <ol className="mt-3 space-y-1.5 text-sm">
            {run.plan.map((step, i) => (
              <li key={`${i}-${step}`} className="flex gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-raised font-mono text-[11px] text-subtle">{i + 1}</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </>
      )}

      <p className="mt-5 text-xs text-subtle">
        All values come from the backend response for this run.
      </p>
    </motion.section>
  )
}
