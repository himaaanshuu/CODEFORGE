import { useId, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import type { PromptReport } from '../../lib/promptScore'
import { fmtK, fmtUsd } from '../../lib/format'
import { Button } from '../ui/Button'

const MODELS = ['Nemotron 3 Ultra', 'Nemotron 3 Super', 'Nemotron 3 Nano']

interface Props {
  value: string
  onChange: (v: string) => void
  report: PromptReport
  model: string
  onModel: (m: string) => void
  onRun: () => void
  onOpenLab: () => void
  disabled?: boolean
  compact?: boolean
}

export function PromptComposer({ value, onChange, report, model, onModel, onRun, onOpenLab, disabled, compact }: Props) {
  const id = useId()
  const [focused, setFocused] = useState(false)
  const canRun = value.trim().length > 0 && !disabled
  return (
    <section aria-labelledby={`${id}-h`}>
      <p className="chip">New task</p>
      <h2 id={`${id}-h`} className="mt-3 font-display text-2xl font-bold tracking-tight sm:text-3xl">
        What should I change?
      </h2>
      <div className={`panel mt-5 overflow-hidden transition-all duration-base ${focused ? 'border-accent shadow-lift' : ''}`}>
        <label htmlFor={id} className="sr-only">Task description</label>
        <textarea
          id={id} value={value} rows={compact ? 3 : 5} disabled={disabled}
          placeholder="Describe the change you want CodeForge to make…"
          onChange={e => onChange(e.target.value)}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); if (canRun) onRun() } }}
          className="block w-full resize-none bg-transparent p-5 text-[0.9375rem] leading-relaxed text-fg placeholder:text-subtle focus:outline-none focus-visible:outline-none disabled:opacity-60"
        />
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t bg-raised/60 px-4 py-2.5 text-xs">
          <button type="button" onClick={onOpenLab} className="rounded-xs text-left" aria-label={`Prompt score ${report.score} out of 100. Open Prompt Lab`}>
            <span className="text-subtle">Prompt score </span>
            <span className="font-mono font-semibold text-ok">{report.score}/100</span>
          </button>
          <span className="font-mono text-subtle" title="Rough estimate before the run">~{fmtK(report.estTokens)} tokens</span>
          <span className="font-mono text-subtle" title="Rough estimate before the run">~{fmtUsd(report.estCost)}</span>
          <span className="ml-auto flex items-center gap-3">
            <span className="relative">
              <label htmlFor={`${id}-m`} className="sr-only">Model</label>
              <select
                id={`${id}-m`} value={model} onChange={e => onModel(e.target.value)}
                className="appearance-none rounded-sm border border-strong bg-surface py-1.5 pl-3 pr-8 font-mono text-xs"
              >
                {MODELS.map(m => <option key={m}>{m}</option>)}
              </select>
              <ChevronDown size={13} aria-hidden className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-subtle" />
            </span>
            <Button size="sm" onClick={onRun} disabled={!canRun} ariaLabel="Run agent">Run agent</Button>
          </span>
        </div>
      </div>
      <p className="mt-2 text-right font-mono text-[0.6875rem] text-subtle">⌘ + Enter to run</p>
    </section>
  )
}
