import { motion } from 'framer-motion'
import { FileCode2, FlaskConical, FolderGit2, GitCompareArrows, Sparkles } from 'lucide-react'
import type { ViewId } from '../../types'

const items: { id: ViewId; label: string; icon: typeof Sparkles }[] = [
  { id: 'repository', label: 'Repository', icon: FolderGit2 },
  { id: 'files', label: 'Files', icon: FileCode2 },
  { id: 'agent', label: 'Agent', icon: Sparkles },
  { id: 'changes', label: 'Changes', icon: GitCompareArrows },
  { id: 'tests', label: 'Tests', icon: FlaskConical },
]

interface Props { view: ViewId; onSelect: (v: ViewId) => void; open: boolean; badges?: Partial<Record<ViewId, string>> }

export function Sidebar({ view, onSelect, open, badges }: Props) {
  return (
    <nav
      id="primary-nav"
      aria-label="Workspace"
      className={`${open ? 'block' : 'hidden'} w-full shrink-0 border-b border-[color:var(--border)] bg-cream md:block md:w-48 md:border-b-0 md:border-r`}
    >
      <p className="eyebrow px-5 pb-2 pt-6">Workspace</p>
      <ul className="pb-4">
        {items.map(({ id, label, icon: Icon }) => {
          const active = view === id
          return (
            <li key={id} className="relative">
              {active && (
                <motion.span layoutId="nav-indicator" className="absolute inset-y-0 left-0 w-0.5 bg-burgundy" transition={{ duration: 0.2 }} />
              )}
              <button
                type="button" onClick={() => onSelect(id)} aria-current={active ? 'page' : undefined}
                className={`flex w-full items-center gap-3 px-5 py-2 text-left text-sm transition-colors duration-fast ${
                  active ? 'bg-ink/[0.05] font-semibold text-ink' : 'text-ink/70 hover:bg-ink/[0.03] hover:text-ink'
                }`}
              >
                <Icon size={15} aria-hidden className={active ? 'text-burgundy' : ''} />
                <span className="flex-1">{label}</span>
                {badges?.[id] && <span className="font-mono text-[0.6875rem] text-muted">{badges[id]}</span>}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
