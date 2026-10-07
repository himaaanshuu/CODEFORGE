import { CodeHeader } from './CodeHeader'
import { HighlightedLine } from './HighlightedLine'

export function CodeViewer({ path, source }: { path: string; source: string }) {
  const lines = source.split('\n')
  return (
    <div className="border border-[color:var(--border)] bg-cream-deep/40">
      <CodeHeader path={path} getText={() => source} />
      <pre className="scroll-thin overflow-x-auto py-3 font-mono text-[0.8125rem] leading-6" tabIndex={0} aria-label={`Contents of ${path}`}>
        <code>
          {lines.map((l, i) => (
            <div key={i} className="flex">
              <span aria-hidden className="w-12 shrink-0 select-none pr-3 text-right text-muted">{i + 1}</span>
              <span aria-hidden className="select-none pr-3 text-[color:var(--border-strong)]">│</span>
              <span className="whitespace-pre pr-4"><HighlightedLine text={l} /></span>
            </div>
          ))}
        </code>
      </pre>
    </div>
  )
}
