import { motion, useReducedMotion } from 'framer-motion'
import type { TaskResult } from '../../types'
import { Button } from '../ui/Button'

interface Props { result: TaskResult; onViewChanges: () => void; onViewTests: () => void }

export function CompletionState({ result, onViewChanges, onViewTests }: Props) {
  const reduce = useReducedMotion()
  const stats = [
    { n: result.filesChanged, label: 'files changed' },
    { n: result.testsPassed, label: 'tests passed' },
    { n: result.regressions, label: 'regressions detected' },
  ]
  return (
    <motion.section
      aria-label="Implementation complete"
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.48, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-3xl px-6 pt-10"
    >
      <div className="border-l-2 border-burgundy pl-6">
        <p className="eyebrow !text-burgundy">Done</p>
        <h2 className="mt-2 font-display text-2xl font-bold tracking-tight sm:text-3xl">IMPLEMENTATION COMPLETE</h2>
        <p className="mt-2 text-sm text-muted">{result.summary}</p>
        <dl className="mt-6 flex flex-wrap gap-x-10 gap-y-4">
          {stats.map((s, i) => (
            <motion.div
              key={s.label}
              initial={reduce ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduce ? 0 : 0.25 + i * 0.1, duration: 0.3 }}
            >
              <dd className="font-display text-3xl font-bold tabular-nums">{s.n}</dd>
              <dt className="text-xs text-muted">{s.label}</dt>
            </motion.div>
          ))}
        </dl>
        <div className="mt-7 flex flex-wrap gap-3">
          <Button onClick={onViewChanges}>VIEW CHANGES</Button>
          <Button variant="ghost" onClick={onViewTests}>VIEW TESTS</Button>
        </div>
      </div>
    </motion.section>
  )
}
