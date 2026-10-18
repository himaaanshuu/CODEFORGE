interface Props {
  size?: 'sm' | 'md' | 'lg'
  onInk?: boolean
  onClick?: () => void
  ariaLabel?: string
}

const sizes = {
  sm: 'text-[0.8125rem]',
  md: 'text-[0.9375rem]',
  lg: 'text-base',
}

export function Brand({ size = 'md', onInk = false, onClick, ariaLabel = 'CodeForge AI home' }: Props) {
  const inner = (
    <span className={`inline-flex items-center gap-2.5 font-display whitespace-nowrap leading-none ${sizes[size]}`}>
      <img src="/logo.png" alt="" aria-hidden className="h-[1.65em] w-auto" draggable={false} />
      <span>
        <span className={`font-bold tracking-[0.18em] ${onInk ? 'text-cream' : 'text-fg'}`}>CODEFORGE</span>{' '}
        <span className={`font-medium tracking-[0.18em] ${onInk ? 'text-burgundy-light' : 'text-accent'}`}>AI</span>
      </span>
    </span>
  )

  if (!onClick) return inner

  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={ariaLabel}
      className="rounded-xs transition-opacity duration-fast hover:opacity-80"
    >
      {inner}
    </button>
  )
}
