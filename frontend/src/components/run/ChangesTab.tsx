import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { FileText } from 'lucide-react'
import type { FileChange } from '../../types'
import { DiffViewer } from '../code/DiffViewer'

export function ChangesTab({ changes }: { changes: FileChange[] }) {
  const reduce = useReducedMotion()
  const [sel, setSel] = useState<string | null>(null)
  if (changes.length === 0) return <p className="py-6 text-sm text-subtle">No changes yet. Modified files appear here once the agent has run.</p>
  const current = changes.find(c => c.path === sel) ?? changes[0]
  return (
    <div className="grid gap-5 py-1 lg:grid-cols-[16rem_1fr]">
      <div className="panel p-3">
        <p className="eyebrow px-1">Files changed ({changes.length})</p>
        <ul className="mt-3 space-y-1">
          {changes.map(c => {
            const on = c.path === current.path
            return (
              <li key={c.path}>
                <button
                  type="button" onClick={() => setSel(c.path)} aria-pressed={on}
                  className={`flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-left font-mono text-xs transition-colors duration-fast hover:bg-raised ${on ? 'bg-accent/12' : ''}`}
                >
                  <FileText size={13} aria-hidden className="shrink-0 text-subtle" />
                  <span className="min-w-0 flex-1 truncate">{c.path}</span>
                  <span className="tabular-nums text-ok">+{c.added}</span>
                  <span className="tabular-nums text-bad">−{c.removed}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </div>
      <div className="min-w-0">
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={current.path}
            initial={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          >
            <DiffViewer change={current} />
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  )
}
