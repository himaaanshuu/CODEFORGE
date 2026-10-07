import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { RepoNode } from '../../types'

interface Props { tree: RepoNode[]; selected: string | null; onSelect: (path: string) => void }

function Node({ node, depth, selected, onSelect }: { node: RepoNode; depth: number } & Omit<Props, 'tree'>) {
  const [open, setOpen] = useState(true)
  const pad = { paddingLeft: `${depth * 14 + 8}px` }
  if (node.type === 'dir') {
    return (
      <li role="none">
        <button
          type="button" role="treeitem" aria-expanded={open}
          onClick={() => setOpen(o => !o)}
          style={pad}
          className="flex w-full items-center gap-1.5 py-1 pr-2 text-left font-mono text-[0.8125rem] transition-colors duration-fast hover:bg-cream-deep"
        >
          {open ? <ChevronDown size={13} aria-hidden /> : <ChevronRight size={13} aria-hidden />}
          {node.name}
        </button>
        {open && (
          <ul role="group">
            {node.children?.map(c => <Node key={c.path} node={c} depth={depth + 1} selected={selected} onSelect={onSelect} />)}
          </ul>
        )}
      </li>
    )
  }
  const isSel = selected === node.path
  return (
    <li role="none">
      <button
        type="button" role="treeitem" aria-selected={isSel}
        onClick={() => onSelect(node.path)}
        style={{ paddingLeft: `${depth * 14 + 8 + 17}px` }}
        className={`flex w-full items-center border-l-2 py-1 pr-2 text-left font-mono text-[0.8125rem] transition-colors duration-fast ${
          isSel ? 'border-burgundy bg-burgundy/[0.07] text-ink' : 'border-transparent text-ink/80 hover:bg-cream-deep'
        }`}
      >
        {node.name}
      </button>
    </li>
  )
}

export function FileExplorer({ tree, selected, onSelect }: Props) {
  return (
    <nav aria-label="Repository files">
      <p className="eyebrow mb-2 px-2">Project</p>
      <ul role="tree" aria-label="Project files">
        {tree.map(n => <Node key={n.path} node={n} depth={0} selected={selected} onSelect={onSelect} />)}
      </ul>
    </nav>
  )
}
