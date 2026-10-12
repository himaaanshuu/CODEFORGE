import { useState } from 'react'
import { ChevronDown, ChevronRight, PencilLine } from 'lucide-react'
import type { RepoNode } from '../../types'

interface Props {
  tree: RepoNode[]
  selected: string | null
  onSelect: (path: string) => void
  changed?: string[]
  title?: string
}

function Node({
  node,
  depth,
  selected,
  onSelect,
  changed,
}: {
  node: RepoNode
  depth: number
  selected: string | null
  onSelect: (path: string) => void
  changed: Set<string>
}) {
  const [open, setOpen] = useState(true)
  const pad = { paddingLeft: `${depth * 14 + 8}px` }
  if (node.type === 'dir') {
    return (
      <li role="none">
        <button
          type="button"
          role="treeitem"
          aria-expanded={open}
          onClick={() => setOpen(o => !o)}
          style={pad}
          className="flex w-full items-center gap-1.5 py-1 pr-2 text-left font-mono text-[0.8125rem] transition-colors duration-fast hover:bg-cream-deep"
        >
          {open ? <ChevronDown size={13} aria-hidden /> : <ChevronRight size={13} aria-hidden />}
          {node.name}
        </button>
        {open && (
          <ul role="group">
            {node.children?.map(c => (
              <Node
                key={c.path}
                node={c}
                depth={depth + 1}
                selected={selected}
                onSelect={onSelect}
                changed={changed}
              />
            ))}
          </ul>
        )}
      </li>
    )
  }
  const isSel = selected === node.path
  const isChanged = changed.has(node.path)
  return (
    <li role="none">
      <button
        type="button"
        role="treeitem"
        aria-selected={isSel}
        onClick={() => onSelect(node.path)}
        style={{ paddingLeft: `${depth * 14 + 8 + 17}px` }}
        className={`flex w-full items-center border-l-2 py-1 pr-2 text-left font-mono text-[0.8125rem] transition-colors duration-fast ${
          isSel
            ? 'border-burgundy bg-burgundy/[0.07] text-ink'
            : 'border-transparent text-ink/80 hover:bg-cream-deep'
        }`}
      >
        <span className="min-w-0 flex-1 truncate">{node.name}</span>
        {isChanged && (
          <span title="Modified by the last agent run" className="ml-1.5 shrink-0 text-burgundy">
            <PencilLine size={11} aria-hidden />
          </span>
        )}
      </button>
    </li>
  )
}

export function FileExplorer({ tree, selected, onSelect, changed, title }: Props) {
  const changedSet = new Set(changed ?? [])
  return (
    <nav aria-label="Repository files">
      <p className="eyebrow mb-2 px-2">{title || 'Project'}</p>
      <ul role="tree" aria-label="Project files">
        {tree.map(n => (
          <Node
            key={n.path}
            node={n}
            depth={0}
            selected={selected}
            onSelect={onSelect}
            changed={changedSet}
          />
        ))}
      </ul>
    </nav>
  )
}
