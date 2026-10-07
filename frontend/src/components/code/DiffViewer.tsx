import type { FileChange } from '../../types'
import { CodeHeader } from './CodeHeader'
import { HighlightedLine } from './HighlightedLine'

const bg = { add: 'bg-[color:var(--diff-add-bg)]', del: 'bg-[color:var(--diff-del-bg)]', context: '' } as const
const mark = { add: '+', del: '−', context: ' ' } as const

export function DiffViewer({ change }: { change: FileChange }) {
  const text = change.lines.filter(l => l.kind !== 'del').map(l => l.text).join('\n')
  return (
    <div className="border border-[color:var(--border)] bg-cream-deep/40">
      <CodeHeader
        path={change.path}
        getText={() => text}
        right={<span className="font-mono text-xs"><span className="text-sage">+{change.added}</span>{' '}<span className="text-rust">−{change.removed}</span></span>}
      />
      <pre className="scroll-thin overflow-x-auto py-3 font-mono text-[0.8125rem] leading-6" tabIndex={0} aria-label={`Diff of ${change.path}`}>
        <code>
          {change.lines.map((l, i) => (
            <div key={i} className={`flex ${bg[l.kind]}`}>
              <span aria-hidden className="w-10 shrink-0 select-none pr-2 text-right text-muted">{l.oldNo ?? ''}</span>
              <span aria-hidden className="w-10 shrink-0 select-none pr-2 text-right text-muted">{l.newNo ?? ''}</span>
              <span className={`w-5 shrink-0 select-none text-center ${l.kind === 'add' ? 'text-sage' : l.kind === 'del' ? 'text-rust' : 'text-muted'}`}>
                <span className="sr-only">{l.kind === 'add' ? 'added: ' : l.kind === 'del' ? 'removed: ' : ''}</span>
                <span aria-hidden>{mark[l.kind]}</span>
              </span>
              <span className="whitespace-pre pr-4"><HighlightedLine text={l.text} /></span>
            </div>
          ))}
        </code>
      </pre>
    </div>
  )
}
