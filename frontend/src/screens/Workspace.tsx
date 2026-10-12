import { useCallback, useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { AgentController } from '../hooks/useAgentRun'
import type { RepoNode, RepoSummary, RunTab, ViewId } from '../types'
import { fetchFile, fetchTree, cloneGitHubRepo } from '../lib/agentClient'
import { fetchGitHubRepos } from '../lib/githubClient'
import { scorePrompt } from '../lib/promptScore'
import { AgentActivity } from '../components/agent/AgentActivity'
import { PromptComposer } from '../components/agent/PromptComposer'
import { ArchitectureMap } from '../components/insights/ArchitectureMap'
import { Efficiency } from '../components/insights/Efficiency'
import { PromptLab } from '../components/insights/PromptLab'
import { UsageDashboard } from '../components/insights/UsageDashboard'
import { FileExplorer } from '../components/repository/FileExplorer'
import { RepoList } from '../components/repository/RepoList'
import { ChangesTab } from '../components/run/ChangesTab'
import { TestsTab } from '../components/run/TestsTab'
import { VerificationTab } from '../components/run/VerificationTab'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Alert'
import { EmptyState } from '../components/ui/EmptyState'
import { Tabs } from '../components/ui/Tabs'

interface Props {
  view: ViewId
  agent: AgentController
  onNavigate: (v: ViewId) => void
}

const DEFAULT_WORKSPACE_ID = 'local-project'

const RUN_TABS: { id: RunTab; label: string }[] = [
  { id: 'activity', label: 'Activity' },
  { id: 'changes', label: 'Changes' },
  { id: 'tests', label: 'Tests' },
  { id: 'verification', label: 'Verification' },
]

function ViewHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div>
      <p className="eyebrow">Workspace</p>
      <h2 className="mt-1 font-display text-2xl font-bold tracking-tight">{title}</h2>
      {subtitle && <p className="mt-2 max-w-xl text-sm text-subtle">{subtitle}</p>}
    </div>
  )
}

export function Workspace({ view, agent, onNavigate }: Props) {
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('Nemotron 3 Ultra')
  const [tab, setTab] = useState<RunTab>('activity')

  const [workspaceId, setWorkspaceId] = useState(DEFAULT_WORKSPACE_ID)
  const [cloningRepo, setCloningRepo] = useState<string | null>(null)
  const [agentFile, setAgentFile] = useState<string | null>(null)

  const [githubRepos, setGithubRepos] = useState<RepoSummary[] | null>(null)
  const [githubError, setGithubError] = useState<string | null>(null)

  const [tree, setTree] = useState<RepoNode | null>(null)
  const [treeError, setTreeError] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<string | null>(null)
  const [fileTruncated, setFileTruncated] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const [fileLoading, setFileLoading] = useState(false)

  const report = useMemo(() => scorePrompt(prompt), [prompt])

  useEffect(() => {
    let alive = true
    fetchGitHubRepos()
      .then((repos) => {
        if (alive) setGithubRepos(repos)
      })
      .catch((err: unknown) => {
        if (alive) setGithubError(err instanceof Error ? err.message : 'Could not load GitHub repositories')
      })
    return () => {
      alive = false
    }
  }, [])

  const loadTree = useCallback(() => {
    setTreeError(null)
    setSelectedFile(null)
    setFileContent(null)
    fetchTree(workspaceId)
      .then(setTree)
      .catch((err: unknown) => setTreeError(err instanceof Error ? err.message : 'Could not load files'))
  }, [workspaceId])

  useEffect(() => {
    loadTree()
  }, [loadTree])

  const openFile = useCallback((path: string) => {
    setSelectedFile(path)
    setFileContent(null)
    setFileError(null)
    setFileTruncated(false)
    setFileLoading(true)
    fetchFile(workspaceId, path)
      .then((payload) => {
        setFileContent(payload.content)
        setFileTruncated(payload.truncated)
      })
      .catch((err: unknown) => setFileError(err instanceof Error ? err.message : 'Could not read file'))
      .finally(() => setFileLoading(false))
  }, [workspaceId])

  const handleRepoSelect = useCallback(async (r: RepoSummary) => {
    setCloningRepo(`${r.owner}/${r.name}`)
    setGithubError(null)
    try {
      const ws = await cloneGitHubRepo(r.owner, r.name)
      setWorkspaceId(ws.id)
      onNavigate('files')
    } catch (err: unknown) {
      setGithubError(err instanceof Error ? err.message : 'Could not clone repository')
    } finally {
      setCloningRepo(null)
    }
  }, [onNavigate])

  const useFileForAgent = useCallback(() => {
    if (!selectedFile) return
    setAgentFile(selectedFile)
    if (!prompt.trim()) {
      setPrompt(`Work on the file ${selectedFile} in the ${workspaceId} workspace.`)
    }
    onNavigate('agent')
  }, [selectedFile, prompt, workspaceId, onNavigate])

  const handleRun = () => {
    const task = prompt.trim()
    if (!task || agent.running) return
    setTab('activity')
    agent.start(task, workspaceId)
  }

  const changedPaths = agent.run?.filesChanged ?? []

  const activitySection = (
    <>
      <AgentActivity events={agent.events} running={agent.running} />
      {agent.run && agent.run.plan.length > 0 && (
        <section aria-label="Plan" className="mt-5 border bg-surface p-4">
          <p className="eyebrow">Plan</p>
          <ol className="mt-2 space-y-1.5">
            {agent.run.plan.map((step, i) => (
              <li key={`${i}-${step}`} className="flex gap-3 text-sm">
                <span className="font-mono text-xs text-subtle">{i + 1}</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </section>
      )}
      {agent.events.length > 0 && (
        <div className="mt-5 flex flex-wrap items-center gap-3">
          <Button variant="ghost" size="sm" onClick={agent.reset}>NEW TASK</Button>
          <Button size="sm" onClick={() => onNavigate('changes')} disabled={!agent.run || agent.run.changes.length === 0}>
            VIEW CHANGES
          </Button>
        </div>
      )}
    </>
  )

  const agentView = (
    <div className="mx-auto max-w-4xl px-6 py-10">
      {agentFile && (
        <p className="mb-4 inline-flex items-center gap-2 border bg-surface px-3 py-1.5 font-mono text-xs text-subtle">
          Target file: <span className="text-ink">{agentFile}</span>
          <button
            type="button"
            onClick={() => setAgentFile(null)}
            aria-label="Clear target file"
            className="text-subtle hover:text-ink"
          >
            ×
          </button>
        </p>
      )}
      <PromptComposer
        value={prompt}
        onChange={setPrompt}
        report={report}
        model={model}
        onModel={setModel}
        onRun={handleRun}
        onOpenLab={() => onNavigate('prompt')}
        disabled={agent.running}
      />
      <div className="mt-8">
        <Tabs<RunTab> label="Run" value={tab} onChange={setTab} tabs={RUN_TABS} />
        <div role="tabpanel" className="min-h-40">
          {tab === 'activity' && activitySection}
          {tab === 'changes' && <ChangesTab changes={agent.run?.changes ?? []} />}
          {tab === 'tests' && <TestsTab run={agent.run?.tests ?? null} />}
          {tab === 'verification' && <VerificationTab run={agent.run} />}
        </div>
      </div>
    </div>
  )

  const repositoriesView = (
    <>
      <div className="mx-auto max-w-3xl px-6 pt-10">
        <ViewHeader
          title="Repository"
          subtitle="Your GitHub repositories. Select one to clone it and browse its files."
        />
        {githubError && (
          <Alert variant="error" title="GitHub" className="mt-6">{githubError}</Alert>
        )}
        {cloningRepo && (
          <Alert variant="info" title="Cloning repository" className="mt-6">
            Cloning <span className="font-mono">{cloningRepo}</span> — large repositories can take a minute…
          </Alert>
        )}
        {githubRepos === null && !githubError && (
          <p className="mt-6 text-sm text-subtle">Loading GitHub repositories…</p>
        )}
        {githubRepos !== null && githubRepos.length === 0 && (
          <p className="mt-6 text-sm text-subtle">
            No repositories returned by GitHub for this account.
          </p>
        )}
      </div>
      {githubRepos !== null && githubRepos.length > 0 && (
        <RepoList
          repos={githubRepos}
          onSelect={handleRepoSelect}
        />
      )}
    </>
  )

  const filesView = (
    <div className="grid lg:grid-cols-[17rem_1fr]">
      <aside className="border-b p-3 lg:border-b-0 lg:border-r">
        {tree ? (
          <FileExplorer
            tree={tree.children ?? []}
            selected={selectedFile}
            onSelect={openFile}
            changed={changedPaths}
            title={tree.name}
          />
        ) : treeError ? (
          <div className="px-2 py-4">
            <Alert variant="error" title="Could not load files">{treeError}</Alert>
            <div className="mt-3">
              <Button variant="ghost" size="sm" onClick={loadTree}>RETRY</Button>
            </div>
          </div>
        ) : (
          <p className="px-2 py-4 text-sm text-subtle">Loading files…</p>
        )}
      </aside>
      <section className="min-w-0 p-6">
        {selectedFile === null ? (
          <EmptyState title="File viewer" message="Select a file on the left to read its real contents from the workspace." />
        ) : fileLoading ? (
          <p className="text-sm text-subtle">Loading {selectedFile}…</p>
        ) : fileError ? (
          <Alert variant="error" title={`Could not read ${selectedFile}`}>{fileError}</Alert>
        ) : (
          <article className="min-w-0">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="eyebrow break-all">{selectedFile}</p>
              <Button size="sm" onClick={useFileForAgent}>USE FOR AGENT</Button>
            </div>
            <pre className="scroll-thin mt-3 overflow-x-auto whitespace-pre-wrap break-words border bg-surface p-4 font-mono text-[0.8125rem] leading-6">
              {fileContent}
              {fileTruncated ? '\n\n… (file truncated)' : ''}
            </pre>
          </article>
        )}
      </section>
    </div>
  )

  const changesView = (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <ViewHeader title="Changes" subtitle="Diff of the files modified by your last agent run." />
      <ChangesTab changes={agent.run?.changes ?? []} />
    </div>
  )

  const testsView = (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <ViewHeader title="Tests" subtitle="Results of the test suite executed during your last run." />
      <TestsTab run={agent.run?.tests ?? null} />
    </div>
  )

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={view}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.18 }}
      >
        {view === 'repositories' && repositoriesView}
        {view === 'files' && filesView}
        {view === 'agent' && agentView}
        {view === 'changes' && changesView}
        {view === 'tests' && testsView}
        {view === 'architecture' && (
          <ArchitectureMap tree={tree} loading={!tree && !treeError} onOpenFile={(path) => {
            onNavigate('files')
            openFile(path)
          }} />
        )}
        {view === 'prompt' && (
          <PromptLab
            prompt={prompt}
            onChange={setPrompt}
            report={report}
            onUse={() => onNavigate('agent')}
          />
        )}
        {view === 'usage' && <UsageDashboard run={agent.run} />}
        {view === 'efficiency' && <Efficiency run={agent.run} />}
      </motion.div>
    </AnimatePresence>
  )
}
