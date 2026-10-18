import { useMemo, useState } from 'react'
import type { RepoNode } from '../../types'
import { Button } from '../ui/Button'
import { EmptyState } from '../ui/EmptyState'

interface Props {
  tree: RepoNode | null
  loading?: boolean
  onOpenFile: (path: string) => void
}

type NodeKind = 'dir' | 'file'

interface MapNode {
  id: string
  label: string
  kind: NodeKind
  path: string
  x: number
  y: number
  isEntry: boolean
  childCount: number
}

const COL = 128
const NH = 30
const LEVEL = 60
const BAND_H = NH + 30
const DOT_PITCH = 14
const DOT_SIZE = 8
const DOTS_PER_ROW = 9
const MAX_BAND = 11
const MAX_DEPTH = 6
const MAX_NODES = 250

const ENTRY_POINTS = new Set([
  'main.py', 'app.py', 'server.py', 'manage.py', 'cli.py', '__main__.py',
  'index.js', 'index.ts', 'index.tsx', 'main.ts', 'main.tsx',
])

/** Clone storage, not part of the project's own architecture. */
const OMIT_DIRS = new Set(['cloned_repos', 'node_modules'])

const shortLabel = (s: string, max = 14) => (s.length > max ? `${s.slice(0, max - 1)}…` : s)

const sortKids = (kids: RepoNode[]) =>
  [...kids].sort((a, b) => {
    if (a.type !== b.type) return a.type === 'dir' ? -1 : 1
    return a.name.localeCompare(b.name)
  })

/**
 * Fit the complete architecture on screen at once.
 *
 * Directories are labelled boxes; files are small dots packed in rows under
 * their directory (accent dots are entry points). Wide sibling levels wrap
 * into horizontal bands so the graph stays within a readable aspect ratio,
 * and the whole thing is drawn into one auto-fitting SVG viewBox — no zoom
 * or scrolling required. Clone-storage directories are omitted.
 */
function buildGraph(root: RepoNode | null): {
  nodes: MapNode[]
  edges: [string, string][]
  truncated: boolean
} {
  const nodes: MapNode[] = []
  const edges: [string, string][] = []
  if (!root) return { nodes, edges, truncated: false }
  let truncated = false

  const visibleKids = (node: RepoNode): RepoNode[] =>
    node.type === 'dir' && node.children
      ? sortKids(node.children).filter(c => !(c.type === 'dir' && OMIT_DIRS.has(c.name)))
      : []

  /** Subtree width in columns. Files contribute ~0 — dots live under the box. */
  const measure = (node: RepoNode, depth: number): number => {
    if (depth > MAX_DEPTH) return 1
    const kids = visibleKids(node)
    const dirSpans = kids.filter(k => k.type === 'dir').map(k => measure(k, depth + 1))
    const hasFiles = kids.some(k => k.type === 'file')
    if (dirSpans.length === 0) return 1
    let bandW = 0
    let maxW = 0
    for (const s of dirSpans) {
      if (bandW + s > MAX_BAND && bandW > 0) {
        maxW = Math.max(maxW, bandW)
        bandW = 0
      }
      bandW += s
    }
    maxW = Math.max(maxW, bandW, hasFiles ? 1 : 0)
    return Math.max(maxW, 1)
  }

  /** Greedy band packing shared by measure and place so they agree. */
  const packBands = (kids: RepoNode[], depth: number) => {
    const spans = kids
      .filter(k => k.type === 'dir')
      .map(k => ({ k, s: measure(k, depth + 1) }))
    const bands: { k: RepoNode; s: number }[][] = [[]]
    let bandW = 0
    for (const it of spans) {
      if (bandW + it.s > MAX_BAND && bandW > 0) {
        bands.push([])
        bandW = 0
      }
      bands[bands.length - 1].push(it)
      bandW += it.s
    }
    return bands
  }

  const place = (
    node: RepoNode,
    depth: number,
    col0: number,
    bandOff: number,
    parent: string | null,
  ): void => {
    if (depth > MAX_DEPTH || nodes.length >= MAX_NODES) {
      if (depth > MAX_DEPTH || parent) truncated = true
      return
    }
    const y = 16 + depth * LEVEL + bandOff
    const kids = visibleKids(node)
    const dirKids = kids.filter(k => k.type === 'dir')
    const fileKids = kids.filter(k => k.type === 'file')
    const bands = packBands(dirKids, depth + 1)

    const w0 = bands[0].reduce((a, i) => a + i.s, 0)
    const parentCol = Math.round(col0 + (Math.max(w0, 1) - 1) / 2)

    bands.forEach((band, bi) => {
      let cur = col0
      for (const it of band) {
        place(it.k, depth + 1, cur, bandOff + bi * BAND_H, node.path)
        cur += it.s
      }
    })

    fileKids.forEach((f, i) => {
      if (nodes.length >= MAX_NODES) {
        truncated = true
        return
      }
      const r = Math.floor(i / DOTS_PER_ROW)
      const c = i % DOTS_PER_ROW
      const k = Math.min(fileKids.length - r * DOTS_PER_ROW, DOTS_PER_ROW)
      const start = parentCol - (k - 1) / 2
      nodes.push({
        id: f.path,
        label: f.name,
        kind: 'file',
        path: f.path,
        x: 16 + (start + c) * COL,
        y: y + NH + 8 + r * DOT_PITCH,
        isEntry: ENTRY_POINTS.has(f.name),
        childCount: 0,
      })
      edges.push([node.path, f.path])
    })

    nodes.push({
      id: node.path,
      label: node.name,
      kind: 'dir',
      path: node.path,
      x: 16 + parentCol * COL,
      y,
      isEntry: false,
      childCount: dirKids.length + fileKids.length,
    })
    if (parent) edges.push([parent, node.path])
  }

  const top = visibleKids(root)
  const topBands = packBands(top, 0)
  topBands.forEach((band, bi) => {
    let cur = 0
    for (const it of band) {
      place(it.k, 0, cur, bi * BAND_H, null)
      cur += it.s
    }
  })
  // Root-level files (e.g. README) as dots under an implied root band.
  const rootFiles = top.filter(k => k.type === 'file')
  if (rootFiles.length > 0) {
    const y = 16 + BAND_H * topBands.length
    rootFiles.forEach((f, i) => {
      if (nodes.length >= MAX_NODES) {
        truncated = true
        return
      }
      const r = Math.floor(i / DOTS_PER_ROW)
      const c = i % DOTS_PER_ROW
      const k = Math.min(rootFiles.length - r * DOTS_PER_ROW, DOTS_PER_ROW)
      const start = Math.floor(topBands[0].reduce((a, i2) => a + i2.s, 0) / 2) - (k - 1) / 2
      nodes.push({
        id: f.path,
        label: f.name,
        kind: 'file',
        path: f.path,
        x: 16 + (start + c) * COL,
        y: y + r * DOT_PITCH,
        isEntry: ENTRY_POINTS.has(f.name),
        childCount: 0,
      })
    })
  }

  return { nodes, edges, truncated }
}

export function ArchitectureMap({ tree, loading, onOpenFile }: Props) {
  const { nodes, edges, truncated } = useMemo(() => buildGraph(tree), [tree])
  const [selected, setSelected] = useState<string | null>(null)

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

  const node = selected ? nodes.find((n) => n.id === selected) : null
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]))
  const width = Math.max(...nodes.map((n) => n.x)) + COL + 16
  const height = Math.max(...nodes.map((n) => n.y)) + NH + 24
  const dirCount = nodes.filter(n => n.kind === 'dir').length
  const fileCount = nodes.filter(n => n.kind === 'file').length
  const entryCount = nodes.filter(n => n.isEntry).length

  return (
    <div className="flex h-[calc(100vh-6.5rem)] min-h-80 flex-col px-4 py-5 sm:px-6">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <div>
          <p className="chip">Workspace</p>
          <h2 className="mt-2 font-display text-xl font-bold tracking-tight">Repository architecture</h2>
        </div>
        <p className="text-xs text-subtle">
          The complete map, fitted to this view — directories as boxes, files as dots.
          {truncated ? ` Showing the first ${nodes.length} entries.` : ''}
        </p>
      </div>

      <div className="mt-3 grid min-h-0 flex-1 gap-4 lg:grid-cols-[1fr_17rem]">
        <div className="panel relative min-h-0 overflow-hidden p-0">
          <svg
            viewBox={`0 0 ${width} ${height}`}
            preserveAspectRatio="xMidYMid meet"
            className="h-full w-full"
            role="img"
            aria-label="Repository architecture map"
          >
            <defs>
              <pattern id="arch-dots" width="16" height="16" patternUnits="userSpaceOnUse">
                <circle cx="1" cy="1" r="1" fill="rgb(var(--fg) / 0.07)" />
              </pattern>
            </defs>
            <rect width={width} height={height} fill="rgb(var(--bg))" />
            <rect width={width} height={height} fill="url(#arch-dots)" />

            {edges.map(([a, b]) => {
              const A = byId[a]
              const B = byId[b]
              if (!A || !B) return null
              const on = node && (node.id === a || node.id === b)
              const sx = A.x + COL / 2
              const sy = A.y + NH
              const ex = B.kind === 'file' ? B.x : B.x + COL / 2
              const ey = B.y
              const midY = sy + Math.max(8, (ey - sy) / 2)
              const d = `M ${sx} ${sy} V ${midY} H ${ex} V ${ey}`
              return (
                <path
                  key={`${a}->${b}`}
                  d={d}
                  fill="none"
                  stroke={on ? 'rgb(var(--accent))' : 'rgb(var(--fg) / 0.18)'}
                  strokeWidth={on ? 1.6 : 1}
                />
              )
            })}

            {nodes.map((n) => {
              const sel = node?.id === n.id
              if (n.kind === 'file') {
                return (
                  <g
                    key={n.id}
                    onClick={() => setSelected(sel ? null : n.id)}
                    className="cursor-pointer"
                  >
                    <title>{n.path}</title>
                    <rect
                      x={n.x - DOT_SIZE / 2 - 2} y={n.y - DOT_SIZE / 2 - 2}
                      width={DOT_SIZE + 4} height={DOT_SIZE + 4}
                      fill="transparent"
                    />
                    <rect
                      x={n.x - DOT_SIZE / 2} y={n.y - DOT_SIZE / 2}
                      width={DOT_SIZE} height={DOT_SIZE} rx={1.5}
                      fill={n.isEntry ? 'rgb(var(--accent))' : 'rgb(var(--muted))'}
                      stroke={sel ? 'rgb(var(--accent))' : 'none'}
                      strokeWidth={sel ? 1.5 : 0}
                    />
                  </g>
                )
              }
              return (
                <g
                  key={n.id}
                  onClick={() => setSelected(sel ? null : n.id)}
                  className="cursor-pointer"
                >
                  <title>{n.path}</title>
                  <rect
                    x={n.x} y={n.y} width={COL - 14} height={NH} rx={4}
                    fill={sel ? 'rgb(var(--accent) / 0.08)' : 'rgb(var(--surface))'}
                    stroke={sel ? 'rgb(var(--accent))' : 'rgb(var(--line-strong))'}
                    strokeWidth={sel ? 1.5 : 1}
                  />
                  <path d={`M ${n.x + 4} ${n.y} H ${n.x + 1} V ${n.y + NH} H ${n.x + 4} Z`} fill="rgb(var(--info))" />
                  <text
                    x={n.x + 10} y={n.y + 13}
                    fontFamily="var(--font-mono)" fontSize={9.5} fontWeight={600}
                    fill="rgb(var(--fg))"
                  >
                    {shortLabel(n.label)}
                  </text>
                  <text
                    x={n.x + 10} y={n.y + 24}
                    fontFamily="var(--font-mono)" fontSize={8}
                    fill="rgb(var(--subtle))"
                  >
                    {n.childCount > 0 ? `${n.childCount}` : 'dir'}
                  </text>
                </g>
              )
            })}
          </svg>

          <ul className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-3 rounded-sm border bg-surface/90 px-3 py-1.5">
            <li className="flex items-center gap-1.5 font-mono text-[10px] text-subtle">
              <span aria-hidden className="h-2.5 w-3 rounded-xs border-l-2 border-info bg-surface" />
              Directory
            </li>
            <li className="flex items-center gap-1.5 font-mono text-[10px] text-subtle">
              <span aria-hidden className="h-2 w-2 rounded-xs bg-accent" />
              Entry file
            </li>
            <li className="flex items-center gap-1.5 font-mono text-[10px] text-subtle">
              <span aria-hidden className="h-2 w-2 rounded-xs bg-muted" />
              File
            </li>
          </ul>
        </div>

        <aside aria-label="Node details" className="panel scroll-thin overflow-auto p-5">
          {node ? (
            <>
              <p className="eyebrow">Node details</p>
              <h3 className="mt-2 break-all font-mono text-sm font-semibold">{node.path}</h3>
              <dl className="mt-4 space-y-3 text-sm">
                <div>
                  <dt className="eyebrow">Kind</dt>
                  <dd className="mt-1">{node.kind === 'dir' ? 'Directory' : node.isEntry ? 'Entry point file' : 'File'}</dd>
                </div>
                <div>
                  <dt className="eyebrow">Location</dt>
                  <dd className="mt-1 break-all font-mono text-xs text-subtle">{node.path}</dd>
                </div>
                {node.kind === 'dir' && (
                  <div>
                    <dt className="eyebrow">Entries</dt>
                    <dd className="mt-1 font-mono text-xs">{node.childCount}</dd>
                  </div>
                )}
              </dl>
              <div className="mt-5">
                <Button
                  full size="sm" disabled={node.kind !== 'file'}
                  onClick={() => onOpenFile(node.path)}
                  title={node.kind === 'file' ? undefined : 'Directories cannot be opened'}
                >
                  OPEN FILE
                </Button>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="mt-3 w-full text-center text-xs text-subtle transition-colors duration-fast hover:text-fg"
              >
                Clear selection
              </button>
            </>
          ) : (
            <>
              <p className="eyebrow">Repository overview</p>
              <dl className="mt-4 space-y-3 text-sm">
                {[
                  ['Directories', String(dirCount)],
                  ['Files', String(fileCount)],
                  ['Entry points', String(entryCount)],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-baseline justify-between border-b border-[color:var(--border)] pb-2">
                    <dt className="text-subtle">{k}</dt>
                    <dd className="font-mono text-xs tabular-nums">{v}</dd>
                  </div>
                ))}
              </dl>
              <p className="mt-5 text-xs leading-relaxed text-subtle">
                Select any box or dot to inspect it and open files from here. Clone storage
                (<span className="font-mono">cloned_repos/</span>) is omitted — it is workspace data, not project architecture.
              </p>
            </>
          )}
        </aside>
      </div>
    </div>
  )
}
