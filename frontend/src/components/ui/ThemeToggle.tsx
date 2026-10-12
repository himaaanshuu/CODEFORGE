import { Moon, Sun } from 'lucide-react'
import type { Theme } from '../../hooks/useTheme'

export function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  const dark = theme === 'dark'
  return (
    <button
      type="button" onClick={onToggle} role="switch" aria-checked={dark}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="inline-flex h-7 w-7 items-center justify-center rounded-sm text-subtle transition-colors duration-fast hover:bg-raised hover:text-fg"
    >
      {dark ? <Sun size={15} aria-hidden /> : <Moon size={15} aria-hidden />}
    </button>
  )
}
