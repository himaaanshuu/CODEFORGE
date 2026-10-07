import { GitBranch } from 'lucide-react'
import type { Repository } from '../../types'

export function RepositoryHeader({ repo }: { repo: Repository }) {
  return (
    <header className="border-b border-[color:var(--border)] pb-6">
      <p className="eyebrow">Repository</p>
      <h2 className="mt-2 font-display text-3xl font-bold tracking-tight">{repo.owner} / {repo.name}</h2>
      <p className="mt-2 max-w-xl text-sm text-muted">{repo.description}</p>
      <dl className="mt-5 flex flex-wrap gap-x-8 gap-y-3 text-sm">
        <div><dt className="eyebrow">Branch</dt><dd className="mt-1 inline-flex items-center gap-1.5 font-mono"><GitBranch size={13} aria-hidden />{repo.branch}</dd></div>
        <div><dt className="eyebrow">Language</dt><dd className="mt-1">{repo.language}</dd></div>
        <div><dt className="eyebrow">Files</dt><dd className="mt-1 tabular-nums">{repo.files}</dd></div>
      </dl>
    </header>
  )
}
