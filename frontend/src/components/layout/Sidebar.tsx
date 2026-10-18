import { motion } from 'framer-motion'
import {
  Braces,
  FileCode2,
  FlaskConical,
  FolderGit2,
  Gauge,
  GitCompareArrows,
  Network,
  Sparkles,
  Timer,
} from 'lucide-react'
import type { ViewId } from '../../types'

const groups: { title: string; items: { id: ViewId; label: string; icon: typeof Sparkles }[] }[] = [
  {
    title: 'Build',
    items: [
      { id: 'agent', label: 'Agent', icon: Sparkles },
      { id: 'repositories', label: 'Repository', icon: FolderGit2 },
      { id: 'files', label: 'Files', icon: FileCode2 },
    ],
  },
  {
    title: 'Run',
    items: [
      { id: 'changes', label: 'Changes', icon: GitCompareArrows },
      { id: 'tests', label: 'Tests', icon: FlaskConical },
    ],
  },
  {
    title: 'Insights',
    items: [
      { id: 'architecture', label: 'Architecture', icon: Network },
      { id: 'prompt', label: 'Prompt Lab', icon: Braces },
      { id: 'usage', label: 'Usage', icon: Gauge },
      { id: 'efficiency', label: 'Efficiency', icon: Timer },
    ],
  },
]

interface Props {
  view: ViewId
  onSelect: (v: ViewId) => void
  open: boolean
  badges?: Partial<Record<ViewId, string>>
}

export function Sidebar({ view, onSelect, open, badges }: Props) {
  return (
    <nav
      id="primary-nav"
      aria-label="Workspace"
      className={`${open ? 'block' : 'hidden'} w-full shrink-0 border-b bg-surface md:block md:w-56 md:border-b-0 md:border-r`}
    >
      <div className="scroll-thin md:h-full md:overflow-y-auto">
        {groups.map((group) => (
          <div key={group.title} className="px-3 pt-5">
            <p className="eyebrow px-2">{group.title}</p>
            <ul className="mt-1.5 space-y-0.5 pb-1">
              {group.items.map(({ id, label, icon: Icon }) => {
                const active = view === id
                return (
                  <li key={id} className="relative">
                    <button
                      type="button"
                      onClick={() => onSelect(id)}
                      aria-current={active ? 'page' : undefined}
                      className={`relative flex w-full items-center gap-2.5 rounded-sm px-2.5 py-2 text-left text-sm transition-colors duration-fast ${
                        active
                          ? 'bg-accent/10 font-semibold text-fg'
                          : 'text-subtle hover:bg-raised hover:text-fg'
                      }`}
                    >
                      {active && (
                        <motion.span
                          layoutId="nav-indicator"
                          className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-accent"
                          transition={{ duration: 0.2 }}
                        />
                      )}
                      <Icon size={15} aria-hidden className={active ? 'text-accent' : ''} />
                      <span className="flex-1">{label}</span>
                      {badges?.[id] && (
                        <span className="rounded-full bg-raised px-1.5 font-mono text-[0.625rem] text-subtle">
                          {badges[id]}
                        </span>
                      )}
                    </button>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </div>
    </nav>
  )
}
