interface Props {
  size?: 'sm' | 'md' | 'lg'
  onInk?: boolean
}

const sizes = {
  sm: 'text-[0.8125rem]',
  md: 'text-[0.9375rem]',
  lg: 'text-base',
}

export function Brand({ size = 'md', onInk = false }: Props) {
  return (
    <span className={`inline-flex items-center gap-2.5 font-display whitespace-nowrap leading-none ${sizes[size]}`}>
      <img src="/logo.png" alt="" aria-hidden className="h-[1.65em] w-auto" draggable={false} />
      <span>
        <span className={`font-bold tracking-[0.18em] ${onInk ? 'text-cream' : 'text-fg'}`}>CODEFORGE</span>{' '}
        <span className={`font-medium tracking-[0.18em] ${onInk ? 'text-burgundy-light' : 'text-accent'}`}>AI</span>
      </span>
    </span>
  )
}
