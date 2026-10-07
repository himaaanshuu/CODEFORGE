import { useId, useState } from 'react'
import { Button } from '../ui/Button'

interface Props {
  repository: string
  disabled?: boolean
  onRun: (task: string) => void
}

const PLACEHOLDER =
  'Fix the authentication flow when JWT tokens expire.'

export function TaskInput({ repository, disabled, onRun }: Props) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)
  const id = useId()
  const canRun = value.trim().length > 0 && !disabled

  const submit = () => { if (canRun) onRun(value.trim()) }

  return (
    <section aria-labelledby={`${id}-h`} className="mx-auto w-full max-w-3xl px-6 py-12 sm:py-20">
      <p className="eyebrow">New task</p>
      <h2 id={`${id}-h`} className="mt-3 font-display text-[clamp(2rem,5vw,3.5rem)] font-bold leading-[1.02] tracking-tight">
        WHAT SHOULD<br />I CHANGE?
      </h2>
      <p className="mt-4 max-w-md text-[0.9375rem] text-muted">
        Describe the coding task. CodeForge will inspect the repository,
        implement the change, run tests, repair failures, and verify the result.
      </p>

      <div
        className={`mt-8 rounded-sm border bg-cream transition-all duration-base ${
          focused ? 'border-burgundy shadow-lift -translate-y-0.5' : 'border-strong shadow-raised'
        }`}
      >
        <label htmlFor={id} className="sr-only">Task description</label>
        <textarea
          id={id}
          value={value}
          rows={6}
          disabled={disabled}
          placeholder={PLACEHOLDER}
          onChange={e => setValue(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); submit() } }}
          className="block w-full resize-none bg-transparent p-5 font-sans text-base leading-relaxed text-ink placeholder:text-muted/80 focus:outline-none focus-visible:outline-none"
        />
        <div className="flex items-center justify-end border-t border-[color:var(--border)] px-4 py-2">
          <kbd className="font-mono text-[0.6875rem] text-muted" aria-label="Command plus Enter to run">⌘ ↵</kbd>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Repository</p>
          <p className="mt-1 font-mono text-sm">{repository}</p>
        </div>
        <Button onClick={submit} disabled={!canRun} ariaLabel="Run agent">RUN AGENT</Button>
      </div>
    </section>
  )
}
