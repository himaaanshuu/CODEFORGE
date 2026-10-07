import { motion, useReducedMotion } from 'framer-motion'
import { Check, X } from 'lucide-react'
import type { TestRun } from '../../types'

export function TestResults({ run }: { run: TestRun | null }) {
  const reduce = useReducedMotion()
  if (!run) {
    return (
      <section aria-label="Test results">
        <h2 className="eyebrow">Test results</h2>
        <p className="mt-4 text-sm text-muted">No test run yet. Results appear after the agent runs the suite.</p>
      </section>
    )
  }
  const passed = run.suites.reduce((n, s) => n + s.passed, 0)
  const failed = run.suites.reduce((n, s) => n + s.failed, 0)
  const total = passed + failed
  return (
    <section aria-label="Test results">
      <h2 className="eyebrow">Test results</h2>
      <ul className="mt-4 border-t border-[color:var(--border)]">
        {run.suites.map((s, i) => {
          const ok = s.failed === 0
          return (
            <motion.li
              key={s.name}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : i * 0.14, duration: 0.28 }}
              className="flex items-center gap-3 border-b border-[color:var(--border)] py-3"
            >
              {ok ? <Check size={15} className="text-sage" aria-label="passed" /> : <X size={15} className="text-rust" aria-label="failed" />}
              <span className="flex-1 text-sm">{s.name}</span>
              <span className={`font-mono text-sm tabular-nums ${ok ? 'text-sage' : 'text-rust'}`}>
                {ok ? `${s.passed} passed` : `${s.failed} failed`}
              </span>
            </motion.li>
          )
        })}
      </ul>
      <motion.div
        initial={reduce ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: reduce ? 0 : run.suites.length * 0.14 + 0.1 }}
        className="mt-6"
      >
        <p className={`font-display text-3xl font-bold tabular-nums ${failed ? 'text-rust' : 'text-ink'}`}>
          {passed} / {total} {failed ? 'PASSED' : 'PASSED'}
        </p>
        <p className="mt-1 font-mono text-xs text-muted">Execution time: {run.durationSeconds.toFixed(2)}s</p>
      </motion.div>
    </section>
  )
}
