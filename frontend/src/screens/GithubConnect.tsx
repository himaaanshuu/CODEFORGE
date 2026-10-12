import { Check } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Logo } from '../components/ui/Logo'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import { GithubMark } from '../components/ui/GithubMark'
import type { Theme } from '../hooks/useTheme'

interface Props { theme: Theme; onToggleTheme: () => void; onConnect: () => void }

const perms = ['Read your repositories', 'Create branches and commits', 'Open pull requests', 'Manage workflow for CodeForge']

export function GithubConnect({ theme, onToggleTheme, onConnect }: Props) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between px-6 py-5">
        <Logo className="text-[0.9375rem]" />
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
      </header>
      <main className="flex flex-1 items-center justify-center px-6 pb-16">
        <section aria-labelledby="gh-h" className="w-full max-w-md border bg-surface p-8 shadow-raised">
          <div className="flex items-center gap-3">
            <GithubMark size={22} />
            <h1 id="gh-h" className="font-display text-xl font-bold tracking-tight">Connect your GitHub account</h1>
          </div>
          <p className="mt-2 text-sm text-subtle">Authorize CodeForge to access your repositories</p>

          <div className="mt-6 flex items-center gap-3 border bg-bg p-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-raised"><GithubMark size={18} /></span>
            <div>
              <p className="text-sm font-semibold">octocat</p>
              <p className="font-mono text-xs text-subtle">@octocat</p>
            </div>
          </div>

          <ul className="mt-6 space-y-2.5">
            {perms.map(p => (
              <li key={p} className="flex items-center gap-3 text-sm"><Check size={15} className="text-ok" aria-hidden />{p}</li>
            ))}
          </ul>
          <div className="mt-7"><Button full onClick={onConnect}>CONNECT GITHUB</Button></div>
          <p className="mt-4 text-center text-xs text-subtle">Preview build: no real GitHub authorization happens yet.</p>
        </section>
      </main>
    </div>
  )
}