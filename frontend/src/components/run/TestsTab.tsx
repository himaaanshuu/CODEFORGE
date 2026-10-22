import { motion, useReducedMotion } from 'framer-motion'
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
  const total = run.passed + run.failed + run.skipped + run.errors
  const status = run.timedOut ? 'Timed out' : run.success ? 'Passed' : 'Failed'
  const output = run.output.trim()
  return (
    <div className="py-1">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <Tile n={status} label="Result" tone={run.success ? 'ok' : 'bad'} />
        <Tile n={String(run.passed)} label="Passed" tone="ok" />
        <Tile n={String(run.failed)} label="Failed" tone={run.failed ? 'bad' : undefined} />
        <Tile n={String(run.skipped)} label="Skipped" />
        <Tile n={String(run.errors)} label="Errors" tone={run.errors ? 'bad' : undefined} />
        <Tile n={`${run.durationSeconds.toFixed(1)}s`} label="Duration" />
      </div>
      <p className="mt-3 text-xs text-subtle">{total} test cases reported</p>
      {total === 0 && (
        <p className="mt-4 text-sm text-subtle">
          The test command ran but reported no test cases. Check its output for collection or command errors.
        </p>
      )}
      {output && (
        <motion.pre
          initial={reduce ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
          className="panel mt-5 max-h-[32rem] overflow-auto whitespace-pre-wrap break-words p-4 font-mono text-xs"
          aria-label="Test command output"
        >
          {output}
        </motion.pre>
      )}
    </div>
  )
}
