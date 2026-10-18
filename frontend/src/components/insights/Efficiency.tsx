import type { AgentRunView } from '../../types'
import { fmtInt } from '../../lib/format'
import { EmptyState } from '../ui/EmptyState'

interface Props {
  run: AgentRunView | null
}

export function Efficiency({ run }: Props) {
  if (!run) {
    return (
      <EmptyState
        title="Efficiency"
        message="Run the agent to see how economically it reached its result. Only real run numbers are shown."
      />
    )
  }

  const m = run.metrics
  const rows: [string, string][] = [
    ['Iterations used', `${m.iterations} of ${m.maxIterations}`],
    ['Tool calls', String(m.toolsUsed.length)],
    ['Files inspected', String(run.filesInspected.length)],
    ['Files changed', String(m.filesChanged)],
    ['Repair attempts', String(m.repairAttempts)],
    ['Wall time', m.durationSeconds > 0 ? `${m.durationSeconds}s` : 'N/A'],
    ['Tokens consumed', m.tokensUsed > 0 ? fmtInt(m.tokensUsed) : 'N/A'],
    ['Result', run.success ? 'Completed' : `Failed (${run.status})`],
  ]

  return (
    <div className="mx-auto max-w-3xl px-5 py-8 sm:px-8">
      <p className="chip">Insights</p>
      <h2 className="mt-3 font-display text-2xl font-bold tracking-tight">Efficiency</h2>
      <p className="mt-2 max-w-md text-sm text-subtle">
        Real numbers from your last run — no sample scoring.
      </p>

      <dl className="panel mt-8 overflow-hidden p-0">
        {rows.map(([label, value]) => (
          <div key={label} className="flex items-baseline justify-between border-b border-[color:var(--line)] px-5 py-3 text-sm last:border-b-0">
            <dt className="text-subtle">{label}</dt>
            <dd className="font-mono tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>

      {m.model && (
        <p className="mt-4 font-mono text-xs text-subtle">Model · {m.model}</p>
      )}
    </div>
  )
}
