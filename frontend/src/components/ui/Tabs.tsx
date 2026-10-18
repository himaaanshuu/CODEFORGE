import { motion } from 'framer-motion'
import { useId } from 'react'

interface Props<T extends string> {
  tabs: { id: T; label: string }[]
  value: T
  onChange: (v: T) => void
  label: string
}

export function Tabs<T extends string>({ tabs, value, onChange, label }: Props<T>) {
  const uid = useId()
  return (
    <div
      role="tablist"
      aria-label={label}
      className="flex flex-wrap gap-1 rounded-sm border bg-raised p-1"
    >
      {tabs.map(t => {
        const on = t.id === value
        return (
          <button
            key={t.id}
            role="tab"
            type="button"
            aria-selected={on}
            id={`${uid}-${t.id}`}
            onClick={() => onChange(t.id)}
            onKeyDown={e => {
              const i = tabs.findIndex(x => x.id === value)
              if (e.key === 'ArrowRight') onChange(tabs[(i + 1) % tabs.length].id)
              if (e.key === 'ArrowLeft') onChange(tabs[(i - 1 + tabs.length) % tabs.length].id)
            }}
            tabIndex={on ? 0 : -1}
            className={`relative rounded-[8px] px-3.5 py-1.5 font-display text-xs font-semibold tracking-[0.06em] transition-colors duration-fast ${
              on ? 'text-fg' : 'text-subtle hover:text-fg'
            }`}
          >
            {on && (
              <motion.span
                layoutId={`${uid}-tab`}
                className="absolute inset-0 rounded-[8px] bg-surface shadow-raised"
                transition={{ duration: 0.2 }}
              />
            )}
            <span className="relative z-10">{t.label}</span>
          </button>
        )
      })}
    </div>
  )
}
