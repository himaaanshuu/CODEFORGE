import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import type { FileChange } from '../../types'
import { DiffViewer } from './DiffViewer'

export function ChangesView({ changes }: { changes: FileChange[] }) {
  const reduce = useReducedMotion()
  const [sel, setSel] = useState<string | null>(null)
  if (changes.length === 0) {
    return (
      <section aria-label="Changes">
        <h2 className="eyebrow">Changes</h2>
        <p className="mt-4 text-sm text-muted">No changes yet. Modified files appear here once the agent finishes.</p>
      </section>
    )
  }
  const current = changes.find(c => c.path === sel) ?? null
  return (
    <section aria-label="Changes">
      <h2 className="eyebrow">Changes</h2>
      <p className="mt-2 font-display text-2xl font-bold tracking-tight">{changes.length} FILES MODIFIED</p>
      <ul className="mt-5 border-t border-[color:var(--border)]">
        {changes.map(c => (
          <li key={c.path} className="border-b border-[color:var(--border)]">
            <button
              type="button"
              onClick={() => setSel(s => (s === c.path ? null : c.path))}
              aria-pressed={sel === c.path}
              className={`flex w-full items-center gap-4 border-l-2 px-3 py-2.5 text-left font-mono text-[0.8125rem] transition-colors duration-fast hover:bg-cream-deep ${
                sel === c.path ? 'border-burgundy bg-burgundy/[0.07]' : 'border-transparent'
              }`}
            >
              <span className="flex-1 truncate">{c.path}</span>
              <span className="tabular-nums text-sage">+{c.added}</span>
              <span className="tabular-nums text-rust">−{c.removed}</span>
            </button>
          </li>
        ))}
      </ul>
      <AnimatePresence mode="wait" initial={false}>
        {current && (
          <motion.div
            key={current.path}
            className="mt-6"
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            <DiffViewer change={current} />
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  )
}
