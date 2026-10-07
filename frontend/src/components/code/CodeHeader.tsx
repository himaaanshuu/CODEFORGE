import { useState } from 'react'
import { Check, Copy } from 'lucide-react'

interface Props { path: string; getText: () => string; right?: React.ReactNode }

export function CodeHeader({ path, getText, right }: Props) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(getText()); setCopied(true); window.setTimeout(() => setCopied(false), 1400) } catch { /* clipboard unavailable */ }
  }
  return (
    <div className="flex items-center justify-between gap-3 border-b border-[color:var(--border)] px-4 py-2.5">
      <span className="truncate font-mono text-xs">{path}</span>
      <div className="flex items-center gap-3">
        {right}
        <button
          type="button"
          onClick={copy}
          aria-label={copied ? 'Copied' : `Copy ${path}`}
          className="inline-flex items-center gap-1.5 rounded-xs px-1.5 py-1 font-display text-[0.6875rem] font-semibold tracking-[0.12em] text-muted transition-colors duration-fast hover:text-ink"
        >
          {copied ? <Check size={13} aria-hidden /> : <Copy size={13} aria-hidden />}
          {copied ? 'COPIED' : 'COPY'}
        </button>
      </div>
    </div>
  )
}
