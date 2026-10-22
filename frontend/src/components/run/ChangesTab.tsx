import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { ExternalLink, FileText, GitBranch, Upload } from 'lucide-react'
import type { FileChange } from '../../types'
import { DiffViewer } from '../code/DiffViewer'
import { fetchWorkspaceDiff, parseUnifiedDiff, publishWorkspaceChanges } from '../../lib/agentClient'
import { getGitHubProviderToken, signInWithGitHub } from '../../lib/supabase'

interface Props {
  changes: FileChange[]
  workspaceId: string | null
  filesChanged: string[]
}

export function ChangesTab({ changes, workspaceId, filesChanged }: Props) {
  const reduce = useReducedMotion()
  const [sel, setSel] = useState<string | null>(null)
  const [showPublish, setShowPublish] = useState(false)
  const [branchName, setBranchName] = useState('update-from-codeforge')
  const [commitMessage, setCommitMessage] = useState('Apply CodeForge agent changes')
  const [publishing, setPublishing] = useState(false)
  const [publishError, setPublishError] = useState<string | null>(null)
  const [published, setPublished] = useState<{ branch: string; commit: string; url: string } | null>(null)
  const [workspaceChanges, setWorkspaceChanges] = useState<FileChange[]>([])
  const [diffLoading, setDiffLoading] = useState(false)
  const [diffError, setDiffError] = useState<string | null>(null)
  const filesKey = filesChanged.join('\n')

  useEffect(() => {
    if (changes.length > 0 || !workspaceId || filesKey.length === 0) {
      setWorkspaceChanges([])
      setDiffLoading(false)
      setDiffError(null)
      return
    }
    let cancelled = false
    setDiffLoading(true)
    setDiffError(null)
    fetchWorkspaceDiff(workspaceId, filesKey.split('\n'))
      .then(result => {
        if (!cancelled) setWorkspaceChanges(parseUnifiedDiff(result.diff))
      })
      .catch(error => {
        if (!cancelled) setDiffError(error instanceof Error ? error.message : 'Could not load workspace diff')
      })
      .finally(() => {
        if (!cancelled) setDiffLoading(false)
      })
    return () => { cancelled = true }
  }, [changes.length, workspaceId, filesKey])

  const publish = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPublishError(null)
    setPublished(null)
    const token = getGitHubProviderToken()
    if (!token) {
      setPublishError('Reconnect GitHub to grant repository write access, then try again.')
      return
    }
    if (!workspaceId || filesChanged.length === 0) {
      setPublishError('No agent-changed files are available for this workspace.')
      return
    }
    setPublishing(true)
    try {
      const result = await publishWorkspaceChanges(
        workspaceId, filesChanged, branchName.trim(), commitMessage.trim(), token,
      )
      setPublished({ branch: result.branch, commit: result.commit, url: result.url })
    } catch (error) {
      setPublishError(error instanceof Error ? error.message : 'Could not push changes to GitHub')
    } finally {
      setPublishing(false)
    }
  }

  const visibleChanges = changes.length > 0 ? changes : workspaceChanges
  if (visibleChanges.length === 0 && filesChanged.length === 0) return <p className="py-6 text-sm text-subtle">No changes yet. Modified files appear here once the agent has run.</p>
  const current = visibleChanges.find(c => c.path === sel) ?? visibleChanges[0]
  return (
    <div className="space-y-5 py-1">
      {current ? <div className="grid gap-5 lg:grid-cols-[16rem_1fr]">
        <div className="panel p-3">
          <p className="eyebrow px-1">Files changed ({visibleChanges.length})</p>
          <ul className="mt-3 space-y-1">
            {visibleChanges.map(c => {
              const on = c.path === current.path
              return (
                <li key={c.path}>
                  <button
                    type="button" onClick={() => setSel(c.path)} aria-pressed={on}
                    className={`flex w-full items-center gap-2 rounded-sm px-2.5 py-2 text-left font-mono text-xs transition-colors duration-fast hover:bg-raised ${on ? 'bg-accent/12' : ''}`}
                  >
                    <FileText size={13} aria-hidden className="shrink-0 text-subtle" />
                    <span className="min-w-0 flex-1 truncate">{c.path}</span>
                    <span className="tabular-nums text-ok">+{c.added}</span>
                    <span className="tabular-nums text-bad">−{c.removed}</span>
                  </button>
                </li>
              )
            })}
          </ul>
        </div>
        <div className="min-w-0">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={current.path}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            >
              <DiffViewer change={current} />
            </motion.div>
          </AnimatePresence>
        </div>
      </div> : (
        <div className="panel p-4 text-sm text-subtle">
          {diffLoading ? 'Loading the current workspace diff…' : diffError ?? 'The changed files have no current diff to review.'}
        </div>
      )}

      {workspaceId && filesChanged.length > 0 && (
        <section className="panel p-4" aria-label="Publish changes to GitHub">
          {!showPublish && !published && (
            <button
              type="button" onClick={() => setShowPublish(true)} disabled={!current || diffLoading}
              className="inline-flex items-center gap-2 rounded-sm bg-burgundy px-4 py-2.5 text-xs font-semibold tracking-wide text-on-accent hover:bg-burgundy-light disabled:opacity-50"
            >
              <Upload size={14} aria-hidden /> {diffLoading ? 'Loading diff…' : 'Commit and push to GitHub'}
            </button>
          )}
          {showPublish && !published && (
            <form onSubmit={publish} className="space-y-4">
              <div>
                <h3 className="font-display text-sm font-semibold">Publish reviewed changes</h3>
                <p className="mt-1 text-xs text-subtle">
                  CodeForge will commit the {filesChanged.length} file(s) changed in this run to a new <code>codex/</code> branch and push that branch. The default branch will not be changed.
                </p>
                <p className="mt-1 text-xs text-subtle">
                  Review each diff first. The commit includes all current unstaged edits in the listed files.
                </p>
              </div>
              <ul className="space-y-1 font-mono text-xs text-subtle">
                {filesChanged.map(path => <li key={path}>{path}</li>)}
              </ul>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-xs text-subtle">
                  Branch name
                  <span className="mt-1 flex items-center gap-2 rounded-sm border border-strong px-3 py-2 text-fg">
                    <GitBranch size={14} aria-hidden className="shrink-0" />
                    <span className="font-mono text-subtle">codex/</span>
                    <input required maxLength={55} pattern="[A-Za-z0-9][A-Za-z0-9._-]*" value={branchName} onChange={event => setBranchName(event.target.value)} className="min-w-0 flex-1 bg-transparent font-mono outline-none" />
                  </span>
                </label>
                <label className="text-xs text-subtle">
                  Commit message
                  <input required maxLength={120} value={commitMessage} onChange={event => setCommitMessage(event.target.value)} className="mt-1 w-full rounded-sm border border-strong bg-transparent px-3 py-2 text-fg outline-none focus:border-burgundy" />
                </label>
              </div>
              {publishError && (
                <div role="alert" className="space-y-2">
                  <p className="text-sm text-bad">{publishError}</p>
                  {/reconnect|authorization|write access/i.test(publishError) && (
                    <button type="button" onClick={() => void signInWithGitHub()} className="text-xs font-semibold text-fg underline underline-offset-4">
                      Reconnect GitHub with repository access
                    </button>
                  )}
                </div>
              )}
              <div className="flex flex-wrap gap-2">
                <button type="submit" disabled={publishing} className="rounded-sm bg-burgundy px-4 py-2.5 text-xs font-semibold tracking-wide text-on-accent hover:bg-burgundy-light disabled:opacity-50">
                  {publishing ? 'Committing and pushing…' : 'Commit and push'}
                </button>
                <button type="button" disabled={publishing} onClick={() => { setShowPublish(false); setPublishError(null) }} className="rounded-sm border border-strong px-4 py-2.5 text-xs font-semibold text-fg hover:bg-raised">
                  Cancel
                </button>
              </div>
            </form>
          )}
          {published && (
            <div role="status" className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm text-ok">Pushed <code>{published.commit}</code> to <code>{published.branch}</code>.</p>
              <a href={published.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs text-fg underline underline-offset-4">
                View branch on GitHub <ExternalLink size={12} aria-hidden />
              </a>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
