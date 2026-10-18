import { motion, useReducedMotion } from 'framer-motion'
import { Check, X } from 'lucide-react'
import type { TestRun } from '../../types'

function Tile({ n, label, tone }: { n: string; label: string; tone?: 'bad' | 'ok' }) {
  return (
    <div className="panel px-5 py-4 text-center">
      <p className={`font-display text-3xl font-bold tabular-nums ${tone === 'bad' ? 'text-bad' : tone === 'ok' ? 'text-ok' : ''}`}>{n}</p>
      <p className="mt-1 text-xs text-subtle">{label}</p>
    </div>
  )
}

export function TestsTab({ run }: { run: TestRun | null }) {
  const reduce = useReducedMotion()
  if (!run) return <p className="py-6 text-sm text-subtle">No test run yet. Results appear after the agent runs the suite.</p>
  const passed = run.tests.filter(t => t.passed).length
  const failed = run.tests.length - passed
  return (
    <div className="py-1">
      <div className="grid grid-cols-3 gap-3">
        <Tile n={String(passed)} label="Passed" tone="ok" />
        <Tile n={String(failed)} label="Failed" tone={failed ? 'bad' : undefined} />
        <Tile n={`${run.durationSeconds.toFixed(1)}s`} label="Duration" />
      </div>
      <ul className="panel mt-5 overflow-hidden p-0" aria-label="Test cases">
        {run.tests.map((t, i) => (
          <motion.li
            key={t.name}
            initial={reduce ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: reduce ? 0 : Math.min(i * 0.025, 0.6), duration: 0.2 }}
            className="flex items-center gap-3 border-b border-[color:var(--line)] px-4 py-2.5 font-mono text-xs last:border-b-0"
          >
            {t.passed ? <Check size={14} className="text-ok" aria-hidden /> : <X size={14} className="text-bad" aria-hidden />}
            <span className="min-w-0 flex-1 truncate">{t.name}</span>
            <span className={`font-semibold tracking-wider ${t.passed ? 'text-ok' : 'text-bad'}`}>{t.passed ? 'PASSED' : 'FAILED'}</span>
            <span className="w-12 text-right tabular-nums text-subtle">{t.seconds.toFixed(2)}s</span>
          </motion.li>
        ))}
      </ul>
    </div>
  )
}
