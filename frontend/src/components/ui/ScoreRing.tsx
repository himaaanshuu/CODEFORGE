import { motion, useReducedMotion } from 'framer-motion'

interface Props { value: number; max?: number; size?: number; label?: string }

/** Circular score. Track is neutral; arc uses the accent. Value is always printed. */
export function ScoreRing({ value, max = 100, size = 120, label }: Props) {
  const reduce = useReducedMotion()
  const r = size / 2 - 7
  const circ = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(1, value / max))
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} role="img" aria-label={`${label ?? 'Score'}: ${value} out of ${max}`}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--fg) / 0.12)" strokeWidth="6" />
        <motion.circle
          cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgb(var(--ok))" strokeWidth="6" strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: reduce ? circ * (1 - pct) : circ }}
          animate={{ strokeDashoffset: circ * (1 - pct) }}
          transition={{ duration: reduce ? 0 : 0.8, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-bold tabular-nums leading-none">{value}</span>
        <span className="mt-1 font-mono text-[0.6875rem] text-subtle">{max}</span>
      </div>
    </div>
  )
}
