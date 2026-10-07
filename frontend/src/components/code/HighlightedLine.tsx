import { tokenClass, tokenize } from '../../lib/highlight'

export function HighlightedLine({ text }: { text: string }) {
  if (!text) return <>{' '}</>
  return <>{tokenize(text).map((t, i) => <span key={i} className={tokenClass[t.kind]}>{t.text}</span>)}</>
}
