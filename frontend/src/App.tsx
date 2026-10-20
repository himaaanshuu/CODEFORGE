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
import type { AuthMode } from './screens/Auth'
import { Docs } from './screens/Docs'

type Route = 'landing' | 'auth' | 'docs' | 'workspace'

export default function App() {
  const agent = useAgentRun()
  const { theme, toggle } = useTheme()
  const auth = useAuth()
  const [route, setRoute] = useState<Route>('landing')
  const [authMode, setAuthMode] = useState<AuthMode>('signup')
  const [view, setView] = useState<ViewId>('agent')
  const [navOpen, setNavOpen] = useState(false)

  const startAuth = (mode: AuthMode = 'signup') => {
    if (auth.status === 'signed-in') {
      setRoute('workspace')
      return
    }
    setAuthMode(mode)
    setRoute('auth')
  }

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
    // No splash/intro screen: the first auth callback resolves immediately
    // from storage, so render nothing rather than an animation overlay.
    return null
  }

  if (route === 'landing') {
    return (
      <Landing
        theme={theme}
        onToggleTheme={toggle}
        onStart={startAuth}
        onDocs={() => setRoute('docs')}
      />
    )
  }

  if (route === 'docs') {
    return (
      <Docs
        theme={theme}
        onToggleTheme={toggle}
        onBack={() => setRoute('landing')}
        onStart={startAuth}
      />
    )
  }

  if (route === 'auth' || auth.status !== 'signed-in') {
    return (
      <Auth
        theme={theme}
        mode={authMode}
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
          onLogoClick={() => setRoute('landing')}
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
