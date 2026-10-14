import { useId } from 'react'

/**
 * CodeForge AI logo mark — metallic CF monogram with glowing code brackets
 * and a sparkle, recreated as scalable SVG (works on light and dark themes).
 */
export function LogoMark({ className = '' }: { className?: string }) {
  const uid = useId().replace(/:/g, '')
  const silver = `${uid}-silver`
  const blue = `${uid}-blue`
  const glow = `${uid}-glow`
  return (
    <svg
      viewBox="0 0 128 96"
      className={className}
      role="img"
      aria-label="CodeForge AI logo"
      fill="none"
    >
      <defs>
        <linearGradient id={silver} x1="0" y1="0" x2="0.25" y2="1">
          <stop offset="0" stopColor="#F1F5F9" />
          <stop offset="0.35" stopColor="#CBD5E1" />
          <stop offset="0.7" stopColor="#64748B" />
          <stop offset="1" stopColor="#3B4A5F" />
        </linearGradient>
        <linearGradient id={blue} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#BAE6FD" />
          <stop offset="0.5" stopColor="#38BDF8" />
          <stop offset="1" stopColor="#0284C7" />
        </linearGradient>
        <filter id={glow} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="2.4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* C — winged crescent */}
      <path
        d="M 64 14 C 32 10 8 28 8 52 C 8 78 32 94 58 88 L 52 76 C 34 80 22 66 22 52 C 22 36 36 26 56 28 L 64 14 Z"
        fill={`url(#${silver})`}
      />

      {/* F — stem and wings */}
      <path d="M 68 18 L 84 14 L 80 86 L 66 90 Z" fill={`url(#${silver})`} />
      <path d="M 66 10 L 128 2 L 128 20 L 76 28 Z" fill={`url(#${silver})`} />
      <path d="M 76 40 L 120 34 L 122 50 L 80 56 Z" fill={`url(#${silver})`} />

      {/* Sparkle */}
      <path
        className="cf-sparkle"
        d="M 72 0 C 74 8 77 11 86 12 C 77 13 74 16 72 24 C 70 16 67 13 58 12 C 67 11 70 8 72 0 Z"
        fill={`url(#${blue})`}
        filter={`url(#${glow})`}
      />

      {/* Code brackets </> */}
      <g
        stroke={`url(#${blue})`}
        strokeWidth="5.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={`url(#${glow})`}
      >
        <path d="M 34 42 L 26 52 L 34 62" />
        <path d="M 46 40 L 36 64" />
        <path d="M 44 42 L 52 52 L 44 62" />
      </g>
    </svg>
  )
}

export function Logo({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-display whitespace-nowrap leading-none ${className}`}>
      <LogoMark className="h-[1.7em] w-auto" />
      <span>
        <span className="font-bold tracking-[0.2em]">CODEFORGE</span>{' '}
        <span className="font-medium tracking-[0.2em] text-accent">AI</span>
      </span>
    </span>
  )
}
