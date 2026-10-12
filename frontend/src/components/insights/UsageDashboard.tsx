import type { AgentRunView } from '../../types'
import { fmtInt } from '../../lib/format'
import { EmptyState } from '../ui/EmptyState'

interface Props {
  run: AgentRunView | null
}

export function UsageDashboard({ run }: Props) {
  if (!run) {
    return (
      <EmptyState
        title="Usage"
        message="Run the agent and real numbers from that run will appear here. Nothing is sampled or faked."
      />
    )
  }

  const m = run.metrics
  const tiles: { label: string; value: string }[] = [
    { label: 'Tokens used', value: m.tokensUsed > 0 ? fmtInt(m.tokensUsed) : 'N/A' },
    { label: 'Wall time', value: m.durationSeconds > 0 ? `${m.durationSeconds}s` : 'N/A' },
    { label: 'Iterations', value: `${m.iterations} / ${m.maxIterations}` },
    { label: 'Tool calls', value: String(m.toolsUsed.length) },
    { label: 'Files inspected', value: String(run.filesInspected.length) },
    { label: 'Estimated cost', value: 'N/A' },
  ]

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">Insights</p>
          <h2 className="mt-1 font-display text-2xl font-bold tracking-tight">Usage dashboard</h2>
        </div>
        <p className="font-mono text-xs text-subtle">
          Last run · {run.status}
          {m.model ? ` · ${m.model}` : ''}
        </p>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-px border bg-[color:var(--line)] sm:grid-cols-3 lg:grid-cols-6">
        {tiles.map((t) => (
          <div key={t.label} className="bg-surface px-4 py-4">
            <dd className="font-display text-2xl font-bold tabular-nums">{t.value}</dd>
            <dt className="mt-1 text-xs text-subtle">{t.label}</dt>
          </div>
        ))}
      </dl>

      <p className="mt-4 text-xs text-subtle">
        Metrics are measured per run by the backend. Cost shows N/A while no pricing table is configured.
      </p>

      <section aria-labelledby="tools-h" className="mt-10">
        <h3 id="tools-h" className="font-display text-base font-semibold">Tools called</h3>
        {m.toolsUsed.length === 0 ? (
          <p className="mt-3 text-sm text-subtle">No tools were called during this run.</p>
        ) : (
          <ul className="mt-3 flex flex-wrap gap-2">
            {m.toolsUsed.map((tool) => (
              <li key={tool} className="border bg-surface px-3 py-1.5 font-mono text-xs">{tool}</li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="insp-h" className="mt-10">
        <h3 id="insp-h" className="font-display text-base font-semibold">Files inspected</h3>
        {run.filesInspected.length === 0 ? (
          <p className="mt-3 text-sm text-subtle">No files were inspected during this run.</p>
        ) : (
          <ul className="mt-3 border-t">
            {run.filesInspected.map((f) => (
              <li key={f} className="border-b py-2 font-mono text-xs">{f}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
