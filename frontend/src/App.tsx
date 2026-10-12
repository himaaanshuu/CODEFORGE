import { useEffect, useState } from 'react'
import type { ViewId } from './types'
import { useAgentRun } from './hooks/useAgentRun'
import { useAuth } from './hooks/useAuth'
import { useTheme } from './hooks/useTheme'
import { AppShell } from './components/layout/AppShell'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { Workspace } from './screens/Workspace'
import { Landing } from './screens/Landing'
import { Auth } from './screens/Auth'

type Route = 'landing' | 'auth' | 'workspace'

export default function App() {
  const agent = useAgentRun()
  const { theme, toggle } = useTheme()
  const auth = useAuth()
  const [route, setRoute] = useState<Route>('landing')
  const [view, setView] = useState<ViewId>('agent')
  const [navOpen, setNavOpen] = useState(false)

  // A signed-in user always lands in the workspace; signing out returns home.
  useEffect(() => {
    if (auth.status === 'signed-in') setRoute('workspace')
    else if (auth.status === 'signed-out') setRoute((r) => (r === 'workspace' ? 'landing' : r))
  }, [auth.status])

  const select = (v: ViewId) => {
    setView(v)
    setNavOpen(false)
  }

  if (auth.status === 'loading') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <p className="font-display text-[0.6875rem] font-semibold tracking-[0.32em] text-subtle">
          CODEFORGE AI
        </p>
      </div>
    )
  }

  if (route === 'landing') {
    return (
      <Landing
        theme={theme}
        onToggleTheme={toggle}
        onStart={() => setRoute('auth')}
      />
    )
  }

  if (route === 'auth' || auth.status !== 'signed-in') {
    return (
      <Auth
        theme={theme}
        onToggleTheme={toggle}
        onBack={() => setRoute('landing')}
      />
    )
  }

  const badges: Partial<Record<ViewId, string>> = {}
  if (agent.run && agent.run.changes.length > 0) {
    badges.changes = String(agent.run.changes.length)
  }
  if (agent.run && agent.run.plan.length > 0) {
    badges.architecture = String(agent.run.plan.length)
  }

  return (
    <AppShell
      state={agent.state}
      lastEvent={agent.events[agent.events.length - 1]}
      header={
        <Header
          state={agent.state}
          navOpen={navOpen}
          onToggleNav={() => setNavOpen(o => !o)}
          theme={theme}
          onToggleTheme={toggle}
          user={auth.user}
        />
      }
      sidebar={
        <Sidebar view={view} onSelect={select} open={navOpen} badges={badges} />
      }
    >
      <Workspace view={view} agent={agent} onNavigate={select} />
    </AppShell>
  )
}
