import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { improvePrompt, scorePrompt, type PromptReport } from '../../lib/promptScore'
import { fmtInt, fmtUsd } from '../../lib/format'
import { Button } from '../ui/Button'
import { ScoreRing } from '../ui/ScoreRing'
import { Tabs } from '../ui/Tabs'

// Static teaching copy for the guide tab (examples, not usage data).
const promptGuide = [
  { title: 'Goal', q: 'What should change?', e: 'Add JWT authentication to the login flow.' },
  { title: 'Context', q: 'Where does it happen?', e: 'In the existing FastAPI app, under app/auth.' },
  { title: 'Constraints', q: 'What must not break?', e: 'Preserve the current login response shape.' },
  { title: 'Acceptance criteria', q: 'How will we know it works?', e: 'Return 401 for invalid or expired tokens.' },
  { title: 'Test expectation', q: 'What should be tested?', e: 'Add tests for token creation and validation.' },
]
const promptWeak = 'Add authentication.'
const promptBetter =
  'Add JWT-based authentication to the existing FastAPI app. Preserve the current login flow, protect user endpoints, return 401 for invalid or expired tokens, and add tests for valid and invalid tokens.'

type LabTab = 'prompt' | 'score' | 'improve' | 'guide'
interface Props { prompt: string; onChange: (v: string) => void; report: PromptReport; onUse: () => void }

export function PromptLab({ prompt, onChange, report, onUse }: Props) {
  const [tab, setTab] = useState<LabTab>('score')
  const [budget, setBudget] = useState(25000)
  const suggestion = improvePrompt(prompt, report)
  const suggestionScore = scorePrompt(suggestion).score
  const missing = report.checks.filter(c => !c.pass)
  const pct = Math.min(100, Math.round((report.estTokens / budget) * 100))

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <p className="eyebrow">Insights</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight">Prompt Lab</h2>
      <div className="mt-5">
        <Tabs<LabTab> label="Prompt Lab" value={tab} onChange={setTab} tabs={[{ id: 'prompt', label: 'Prompt' }, { id: 'score', label: 'Score' }, { id: 'improve', label: 'Improve' }, { id: 'guide', label: 'Guide' }]} />
      </div>

      {tab === 'prompt' && (
        <div className="py-6">
          <label htmlFor="lab-prompt" className="eyebrow">Your prompt</label>
          <textarea id="lab-prompt" rows={6} value={prompt} onChange={e => onChange(e.target.value)} className="field mt-2 resize-none text-sm leading-relaxed" placeholder="Describe the change you want CodeForge to make…" />
          <div className="mt-4 flex items-center justify-between">
            <p className="text-sm text-subtle">Score <span className="font-mono font-semibold text-ok">{report.score}/100</span></p>
            <Button size="sm" onClick={onUse}>USE IN AGENT</Button>
          </div>
        </div>
      )}

      {tab === 'score' && (
        <div className="py-6">
          <div className="flex flex-wrap items-center gap-8">
            <div className="text-center"><ScoreRing value={report.score} label="Prompt quality" /><p className="mt-2 text-xs text-subtle">Prompt quality</p></div>
            <ul className="min-w-[14rem] flex-1 space-y-2.5 text-sm">
              {report.checks.map(c => (
                <li key={c.id} className="flex items-center gap-3">
                  {c.pass ? <Check size={15} className="text-ok" aria-hidden /> : <X size={15} className="text-bad" aria-hidden />}
                  <span className={c.pass ? '' : 'text-subtle'}>{c.label}</span><span className="sr-only">{c.pass ? 'met' : 'missing'}</span>
                </li>
              ))}
            </ul>
          </div>
          {missing.length > 0 && <p className="mt-5 text-sm text-warn"><span className="font-semibold">Missing:</span> {missing.map(m => m.hint).join(' ')}</p>}
          <dl className="mt-6 grid grid-cols-2 border-t pt-5">
            <div><dd className="font-display text-xl font-bold tabular-nums">~{fmtInt(report.estTokens)}</dd><dt className="text-xs text-subtle">Est. request tokens (incl. agent overhead)</dt></div>
            <div><dd className="font-display text-xl font-bold tabular-nums">~{fmtUsd(report.estCost)}</dd><dt className="text-xs text-subtle">Estimated cost</dt></div>
          </dl>
          <div className="mt-6">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="budget" className="text-subtle">Token budget</label>
              <select id="budget" value={budget} onChange={e => setBudget(Number(e.target.value))} className="rounded-sm border border-strong bg-bg px-2 py-1 font-mono">
                {[10000, 25000, 50000].map(b => <option key={b} value={b}>{b / 1000}K</option>)}
              </select>
            </div>
            <div className="mt-2 h-1.5 bg-fg/10" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Estimated share of token budget">
              <div className="h-full bg-ok transition-[width] duration-base" style={{ width: `${pct}%` }} />
            </div>
            <p className="mt-1.5 text-right font-mono text-xs text-subtle">{pct}% of budget</p>
          </div>
          <p className="mt-5 text-xs text-subtle">Scored locally by a simple checklist, not by a model.</p>
        </div>
      )}

      {tab === 'improve' && (
        <div className="py-6">
          <p className="text-sm text-subtle">Your prompt <span className="font-mono text-fg">(Score: {report.score}/100)</span></p>
          <p className="mt-2 border bg-surface p-4 text-sm">{prompt.trim() || <span className="text-subtle">Nothing written yet.</span>}</p>
          {missing.length > 0 ? (
            <>
              <p className="eyebrow mt-6">Issues</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">{missing.map(m => <li key={m.id}>{m.label} — <span className="text-subtle">{m.hint}</span></li>)}</ul>
            </>
          ) : <p className="mt-6 text-sm text-ok">No issues found.</p>}
          <p className="mt-6 text-sm text-subtle">Suggested improved prompt <span className="font-mono text-fg">(Score: {suggestionScore}/100)</span></p>
          <p className="mt-2 border border-ok/50 bg-surface p-4 text-sm">{suggestion}</p>
          <div className="mt-5 flex gap-3">
            <Button onClick={() => { onChange(suggestion); onUse() }} disabled={!prompt.trim()}>APPLY IMPROVED PROMPT</Button>
            <Button variant="ghost" onClick={onUse}>KEEP ORIGINAL</Button>
          </div>
        </div>
      )}

      {tab === 'guide' && (
        <div className="grid gap-8 py-6 md:grid-cols-[1fr_1fr]">
          <ol className="space-y-4">
            {promptGuide.map((g, i) => (
              <li key={g.title} className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-strong font-mono text-xs">{i + 1}</span>
                <div><p className="text-sm font-semibold">{g.title}</p><p className="text-xs text-subtle">{g.q}</p><p className="mt-0.5 text-xs italic">“{g.e}”</p></div>
              </li>
            ))}
          </ol>
          <div className="space-y-4">
            <div className="border p-4"><p className="eyebrow !text-bad">Weak</p><p className="mt-2 text-sm">{promptWeak}</p></div>
            <div className="border border-ok/50 p-4"><p className="eyebrow !text-ok">Better</p><p className="mt-2 text-sm">{promptBetter}</p></div>
          </div>
        </div>
      )}
    </div>
  )
}
