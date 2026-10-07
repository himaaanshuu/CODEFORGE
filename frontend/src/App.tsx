import { useCallback, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import type { ViewId } from './types'
import { mockRepository, mockSources } from './data/mockAgent'
import { useAgentRun } from './hooks/useAgentRun'
import { IntroAnimation } from './components/intro/IntroAnimation'
import { AppShell } from './components/layout/AppShell'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { TaskInput } from './components/agent/TaskInput'
import { AgentActivity } from './components/agent/AgentActivity'
import { CompletionState } from './components/agent/CompletionState'
import { RepositoryHeader } from './components/repository/RepositoryHeader'
import { FileExplorer } from './components/repository/FileExplorer'
import { CodeViewer } from './components/code/CodeViewer'
import { ChangesView } from './components/code/ChangesView'
import { TestResults } from './components/tests/TestResults'

const repo = mockRepository

export default function App() {
  const reduce = useReducedMotion()
  const [introDone, setIntroDone] = useState(false)
  const [view, setView] = useState<ViewId>('agent')
  const [navOpen, setNavOpen] = useState(false)
  const [file, setFile] = useState<string | null>('src/auth/session.ts')
  const agent = useAgentRun()
  const finishIntro = useCallback(() => setIntroDone(true), [])

  const select = (v: ViewId) => { setView(v); setNavOpen(false) }
  const hasRun = agent.events.length > 0

  const badges = agent.run ? { changes: String(agent.run.changes.length), tests: '42' } : undefined

  const body = (() => {
    switch (view) {
      case 'repository':
        return (
          <div className="mx-auto max-w-3xl px-6 py-10">
            <RepositoryHeader repo={repo} />
            <div className="mt-8 max-w-sm"><FileExplorer tree={repo.tree} selected={file} onSelect={p => { setFile(p); setView('files') }} /></div>
          </div>
        )
      case 'files':
        return (
          <div className="mx-auto flex max-w-5xl flex-col gap-8 px-6 py-10 lg:flex-row">
            <div className="lg:w-60 lg:shrink-0"><FileExplorer tree={repo.tree} selected={file} onSelect={setFile} /></div>
            <div className="min-w-0 flex-1">
              {file && mockSources[file] !== undefined
                ? <CodeViewer path={file} source={mockSources[file]} />
                : <p className="text-sm text-muted">Select a file to view its contents.</p>}
            </div>
          </div>
        )
      case 'changes':
        return <div className="mx-auto max-w-3xl px-6 py-10"><ChangesView changes={agent.run?.changes ?? []} /></div>
      case 'tests':
        return <div className="mx-auto max-w-3xl px-6 py-10"><TestResults run={agent.run?.tests ?? null} /></div>
      default:
        return (
          <>
            {!hasRun && <TaskInput repository={repo.name} onRun={agent.start} />}
            {hasRun && (
              <>
                <div className="mx-auto flex max-w-3xl items-center justify-between px-6 pt-10">
                  <h2 className="font-display text-2xl font-bold tracking-tight">TASK RUN</h2>
                  {!agent.running && <button type="button" onClick={agent.reset} className="font-display text-[0.6875rem] font-semibold tracking-[0.14em] text-muted underline-offset-4 hover:text-ink hover:underline">NEW TASK</button>}
                </div>
                <AgentActivity events={agent.events} running={agent.running} />
                {agent.run && <CompletionState result={agent.run.result} onViewChanges={() => select('changes')} onViewTests={() => select('tests')} />}
                <div className="h-12" />
              </>
            )}
          </>
        )
    }
  })()

  return (
    <>
      <AnimatePresence>{!introDone && <IntroAnimation key="intro" onDone={finishIntro} />}</AnimatePresence>
      {introDone && (
        <AppShell
          state={agent.state}
          lastEvent={agent.events[agent.events.length - 1]}
          header={<Header repoPath={`${repo.owner} / ${repo.name}`} state={agent.state} navOpen={navOpen} onToggleNav={() => setNavOpen(o => !o)} />}
          sidebar={<Sidebar view={view} onSelect={select} open={navOpen} badges={badges} />}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={view}
              initial={reduce ? { opacity: 0 } : { opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18 }}
            >
              {body}
            </motion.div>
          </AnimatePresence>
        </AppShell>
      )}
    </>
  )
}
