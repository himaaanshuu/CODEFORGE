import { Moon, Sun } from 'lucide-react'
import type { Theme } from '../../hooks/useTheme'

export function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  const dark = theme === 'dark'
  return (
    <button
      type="button"
      onClick={onToggle}
      role="switch"
      aria-checked={dark}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="inline-flex h-8 items-center gap-1.5 rounded-full border border-strong bg-raised px-1.5 text-subtle transition-colors duration-fast hover:text-fg"
    >
      <span
        className={`flex h-5 w-5 items-center justify-center rounded-full transition-colors duration-fast ${
          dark ? '' : 'bg-surface text-fg shadow-raised'
        }`}
      >
        <Sun size={12} aria-hidden />
      </span>
      <span
        className={`flex h-5 w-5 items-center justify-center rounded-full transition-colors duration-fast ${
          dark ? 'bg-surface text-fg shadow-raised' : ''
        }`}
      >
        <Moon size={12} aria-hidden />
      </span>
    </button>
  )
}
