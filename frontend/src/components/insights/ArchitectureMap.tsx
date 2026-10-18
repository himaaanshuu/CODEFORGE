import { useMemo, useState } from 'react'
import { Maximize2, Minus, Plus } from 'lucide-react'
import type { RepoNode } from '../../types'
import { Button } from '../ui/Button'
import { EmptyState } from '../ui/EmptyState'

interface Props {
  tree: RepoNode | null
  loading?: boolean
  onOpenFile: (path: string) => void
}

interface MapNode {
  id: string
  label: string
  kind: 'Entry point' | 'Directory' | 'File'
  path: string
  x: number
  y: number
  children: number
  isFile: boolean
}

const NW = 150
const NH = 46
const COL = 172
const LEVEL = 84
const MAX_DEPTH = 5
const MAX_NODES = 80

const ENTRY_POINTS = new Set([
  'main.py', 'app.py', 'server.py', 'manage.py', 'cli.py', '__main__.py',
  'index.js', 'index.ts', 'index.tsx', 'main.ts', 'main.tsx',
])

const kindColor: Record<MapNode['kind'], string> = {
  'Entry point': 'border-l-accent',
  Directory: 'border-l-info',
  File: 'border-l-subtle',
}

/**
 * Lay the real file tree out as a tidy top-down graph.
 *
 * Depth runs vertically (root at the top); siblings spread horizontally.
 * Directories sort before files; a directory is horizontally centred over
 * its children (subtree-aware layout), and edges are drawn as orthogonal
 * elbows so parent→child containment is easy to follow.
 */
function buildGraph(root: RepoNode | null): {
  nodes: MapNode[]
  edges: [string, string][]
  truncated: boolean
} {
  const nodes: MapNode[] = []
  const edges: [string, string][] = []
  if (!root) return { nodes, edges, truncated: false }
  let nextCol = 0
  let truncated = false

  const sortKids = (kids: RepoNode[]) =>
    [...kids].sort((a, b) => {
      if (a.type !== b.type) return a.type === 'dir' ? -1 : 1
      return a.name.localeCompare(b.name)
    })

  const walk = (node: RepoNode, depth: number, parent?: string): number | null => {
    if (depth > MAX_DEPTH) return null
    if (nodes.length >= MAX_NODES) {
      truncated = true
      return null
    }
    if (node.type === 'dir' && depth === MAX_DEPTH && (node.children?.length ?? 0) > 0) {
      truncated = true
      return null
    }

    const kids = node.type === 'dir' && node.children ? sortKids(node.children) : []
    const spans: number[] = []
    for (const child of kids) {
      const span = walk(child, depth + 1, node.path)
      if (span !== null) spans.push(span)
    }

    const isFile = node.type === 'file'
    const kind: MapNode['kind'] = isFile
      ? (ENTRY_POINTS.has(node.name) ? 'Entry point' : 'File')
      : 'Directory'

    // Leaves take the next free column; parents centre over their children.
    const col = spans.length > 0
      ? Math.round((spans[0] + spans[spans.length - 1]) / 2)
      : nextCol++

    nodes.push({
      id: node.path,
      label: node.name,
      kind,
      path: node.path,
      x: 24 + col * COL,
      y: 16 + depth * LEVEL,
      children: node.children?.length ?? 0,
      isFile,
    })
    if (parent) edges.push([parent, node.path])
    return col
  }

  root.children?.forEach((child) => walk(child, 0))
  return { nodes, edges, truncated }
}

export function ArchitectureMap({ tree, loading, onOpenFile }: Props) {
  const { nodes, edges, truncated } = useMemo(() => buildGraph(tree), [tree])
  const [selected, setSelected] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)

  if (loading) {
    return <EmptyState title="Architecture" message="Loading the real repository structure…" />
  }
  if (nodes.length === 0) {
    return (
      <EmptyState
        title="Architecture"
        message="The workspace tree could not be loaded, so there is nothing to map yet."
      />
    )
  }

  const node = nodes.find((n) => n.id === selected) ?? nodes[0]
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]))
  const width = Math.max(...nodes.map((n) => n.x)) + NW + 48
  const height = Math.max(...nodes.map((n) => n.y)) + NH + 36
  const clamp = (z: number) => Math.max(0.6, Math.min(1.6, Math.round(z * 10) / 10))
  const ctl = 'flex h-8 w-8 items-center justify-center rounded-sm border bg-surface text-subtle transition-colors duration-fast hover:bg-raised hover:text-fg'
  const hidden = truncated ? `Showing the first ${nodes.length} entries — deeper or extra siblings are omitted.` : ''

  return (
    <div className="flex h-[calc(100vh-6.5rem)] min-h-80 flex-col px-4 py-5 sm:px-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <div>
          <p className="chip">Workspace</p>
          <h2 className="mt-2 font-display text-xl font-bold tracking-tight">Repository architecture</h2>
        </div>
        <p className="text-xs text-subtle">
          Built from the real file tree. Select a node to inspect it.
          {hidden ? ` ${hidden}` : ''}
        </p>
      </div>

      <div className="mt-3 grid min-h-0 flex-1 gap-4 lg:grid-cols-[1fr_17rem]">
        <div className="panel relative min-h-0 overflow-auto scroll-thin p-0">
          <div className="absolute left-3 top-3 z-10 flex flex-col gap-1">
            <button type="button" className={ctl} aria-label="Zoom in" onClick={() => setZoom(z => clamp(z + 0.2))}><Plus size={14} aria-hidden /></button>
            <button type="button" className={ctl} aria-label="Zoom out" onClick={() => setZoom(z => clamp(z - 0.2))}><Minus size={14} aria-hidden /></button>
            <button type="button" className={ctl} aria-label="Reset view" onClick={() => setZoom(1)}><Maximize2 size={13} aria-hidden /></button>
          </div>
          <div
            className="relative origin-top-left transition-transform duration-base"
            style={{ width, height, transform: `scale(${zoom})`, marginLeft: 56 }}
          >
            <svg width={width} height={height} className="absolute inset-0" aria-hidden>
              {edges.map(([a, b]) => {
                const A = byId[a]
                const B = byId[b]
                if (!A || !B) return null
                const on = node.id === a || node.id === b
                // Vertical elbow: out of the parent's bottom edge, down, across, down into the child.
                const sx = A.x + NW / 2
                const sy = A.y + NH
                const ex = B.x + NW / 2
                const ey = B.y
                const midY = sy + Math.max(14, (ey - sy) / 2)
                const d = `M ${sx} ${sy} V ${midY} H ${ex} V ${ey}`
                return (
                  <path
                    key={`${a}->${b}`}
                    d={d}
                    fill="none"
                    stroke={on ? 'rgb(var(--accent))' : 'rgb(var(--fg) / 0.22)'}
                    strokeWidth={on ? 1.75 : 1}
                  />
                )
              })}
            </svg>
            {nodes.map((n) => (
              <button
                key={n.id} type="button"
                onClick={() => setSelected(n.id)}
                aria-pressed={node.id === n.id}
                style={{ left: n.x, top: n.y, width: NW, height: NH }}
                className={`absolute flex flex-col justify-center rounded-sm border border-l-4 bg-bg px-3 text-left transition-colors duration-fast hover:bg-raised ${kindColor[n.kind]} ${node.id === n.id ? 'border-accent ring-1 ring-accent' : ''}`}
              >
                <span className="truncate font-mono text-xs font-semibold">{n.label}</span>
                <span className="truncate text-[0.625rem] text-subtle">
                  {n.kind}{!n.isFile ? ` · ${n.children} ${n.children === 1 ? 'entry' : 'entries'}` : ''}
                </span>
              </button>
            ))}
          </div>
        </div>

        <aside aria-label="Node details" className="panel scroll-thin overflow-auto p-5">
          <p className="eyebrow">Node details</p>
          <h3 className="mt-2 break-all font-mono text-sm font-semibold">{node.path}</h3>
          <dl className="mt-4 space-y-3 text-sm">
            <div>
              <dt className="eyebrow">Kind</dt>
              <dd className="mt-1">{node.kind}</dd>
            </div>
            <div>
              <dt className="eyebrow">Location</dt>
              <dd className="mt-1 break-all font-mono text-xs text-subtle">{node.path}</dd>
            </div>
            {node.isFile ? null : (
              <div>
                <dt className="eyebrow">Entries</dt>
                <dd className="mt-1 font-mono text-xs">{node.children}</dd>
              </div>
            )}
          </dl>
          <div className="mt-5">
            <Button
              full size="sm" disabled={!node.isFile}
              onClick={() => onOpenFile(node.path)}
              title={node.isFile ? undefined : 'Directories cannot be opened'}
            >
              OPEN FILE
            </Button>
          </div>
        </aside>
      </div>
    </div>
  )
}
