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
    <div role="tablist" aria-label={label} className="flex gap-6 border-b">
      {tabs.map(t => {
        const on = t.id === value
        return (
          <button
            key={t.id} role="tab" type="button" aria-selected={on} id={`${uid}-${t.id}`}
            onClick={() => onChange(t.id)}
            onKeyDown={e => {
              const i = tabs.findIndex(x => x.id === value)
              if (e.key === 'ArrowRight') onChange(tabs[(i + 1) % tabs.length].id)
              if (e.key === 'ArrowLeft') onChange(tabs[(i - 1 + tabs.length) % tabs.length].id)
            }}
            tabIndex={on ? 0 : -1}
            className={`relative -mb-px py-2.5 font-display text-xs font-semibold tracking-[0.06em] transition-colors duration-fast ${on ? 'text-fg' : 'text-subtle hover:text-fg'}`}
          >
            {t.label}
            {on && <motion.span layoutId={`${uid}-tab`} className="absolute inset-x-0 bottom-0 h-0.5 bg-accent" transition={{ duration: 0.2 }} />}
          </button>
        )
      })}
    </div>
  )
}
