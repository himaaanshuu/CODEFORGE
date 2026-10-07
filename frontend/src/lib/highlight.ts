/** Tiny dependency-free tokenizer for TS/JS/JSON-ish text. Muted palette via CSS vars. */
export type TokenKind = 'keyword' | 'string' | 'comment' | 'number' | 'fn' | 'plain'
export interface Token { kind: TokenKind; text: string }

const KEYWORDS = new Set([
  'export','async','function','const','let','var','return','if','else','throw','new','await','import','from',
  'describe','it','type','interface','true','false','null','undefined','for','of','class','extends',
])
const RE = /(\/\/.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)|(\b\d+(?:\.\d+)?\b)|([A-Za-z_$][\w$]*)(\s*\()?|(\s+|[^\sA-Za-z_$\d]+)/g

export function tokenize(line: string): Token[] {
  const out: Token[] = []
  for (const m of line.matchAll(RE)) {
    if (m[1]) out.push({ kind: 'comment', text: m[1] })
    else if (m[2]) out.push({ kind: 'string', text: m[2] })
    else if (m[3]) out.push({ kind: 'number', text: m[3] })
    else if (m[4]) {
      const kind: TokenKind = KEYWORDS.has(m[4]) ? 'keyword' : m[5] ? 'fn' : 'plain'
      out.push({ kind, text: m[4] })
      if (m[5]) out.push({ kind: 'plain', text: m[5] })
    } else out.push({ kind: 'plain', text: m[6] ?? m[0] })
  }
  return out
}

export const tokenClass: Record<TokenKind, string> = {
  keyword: 'text-[color:var(--syn-keyword)]',
  string: 'text-[color:var(--syn-string)]',
  comment: 'italic text-[color:var(--syn-comment)]',
  number: 'text-[color:var(--syn-number)]',
  fn: 'text-[color:var(--syn-fn)]',
  plain: '',
}
