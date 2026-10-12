import { useMemo, useState } from 'react'
import { Search, Star } from 'lucide-react'
import type { RepoSummary } from '../../types'
import { Button } from '../ui/Button'
import { GithubMark } from '../ui/GithubMark'

export function RepoList({ repos, onSelect }: { repos: RepoSummary[]; onSelect: (r: RepoSummary) => void }) {
  const [q, setQ] = useState('')
  const shown = useMemo(() => repos.filter(r => `${r.owner}/${r.name}`.toLowerCase().includes(q.toLowerCase())), [repos, q])
  return (
    <section aria-labelledby="repos-h" className="mx-auto max-w-3xl px-6 py-10">
      <h2 id="repos-h" className="font-display text-2xl font-bold tracking-tight">Select a repository</h2>
      <div className="relative mt-5">
        <Search size={15} aria-hidden className="absolute left-3 top-1/2 -translate-y-1/2 text-subtle" />
        <label htmlFor="repo-q" className="sr-only">Search repositories</label>
        <input id="repo-q" value={q} onChange={e => setQ(e.target.value)} placeholder="Search repositories…" className="field pl-9 text-sm" />
      </div>
      <ul className="mt-5 border-t">
        {shown.map(r => (
          <li key={r.name} className="flex items-center gap-4 border-b py-4">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm border"><GithubMark size={16} /></span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">{r.name}</p>
              <p className="truncate font-mono text-xs text-subtle">{r.owner}/{r.name}</p>
              <p className="mt-1 flex flex-wrap items-center gap-x-4 text-xs text-subtle">
                <span className="inline-flex items-center gap-1.5"><span aria-hidden className={`h-2 w-2 rounded-full ${r.language === 'Python' ? 'bg-info' : 'bg-accent'}`} />{r.language}</span>
                <span className="inline-flex items-center gap-1"><Star size={11} aria-hidden />{r.stars}</span>
                <span>Updated {r.updated}</span>
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => onSelect(r)} ariaLabel={`Select ${r.name}`}>SELECT</Button>
          </li>
        ))}
        {shown.length === 0 && <li className="py-6 text-sm text-subtle">No repositories match “{q}”.</li>}
      </ul>
    </section>
  )
}
