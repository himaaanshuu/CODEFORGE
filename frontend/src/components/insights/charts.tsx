import { useMemo, useRef, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

/* ---------- Line chart: two series, hover crosshair + tooltip ---------- */
interface Pt { day: number; input: number; output: number }
const W = 960, H = 250, PL = 44, PR = 28, PT = 12, PB = 28

export function TokenLineChart({ data }: { data: Pt[] }) {
  const ref = useRef<SVGSVGElement>(null)
  const [hover, setHover] = useState<number | null>(null)
  const max = 220
  const x = (i: number) => PL + (i / (data.length - 1)) * (W - PL - PR)
  const y = (v: number) => PT + (1 - v / max) * (H - PT - PB)
  const path = (k: 'input' | 'output') => data.map((d, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(d[k]).toFixed(1)}`).join(' ')
  const onMove = (e: React.PointerEvent) => {
    const r = ref.current!.getBoundingClientRect()
    const px = ((e.clientX - r.left) / r.width) * W
    setHover(Math.max(0, Math.min(data.length - 1, Math.round(((px - PL) / (W - PL - PR)) * (data.length - 1)))))
  }
  const h = hover != null ? data[hover] : null
  return (
    <div className="relative">
      <svg
        ref={ref} viewBox={`0 0 ${W} ${H}`} className="w-full touch-none" role="img"
        aria-label="Daily token usage for October, input and output, in thousands of tokens"
        onPointerMove={onMove} onPointerLeave={() => setHover(null)}
      >
        {[0, 100, 200].map(t => (
          <g key={t}>
            <line x1={PL} x2={W - PR} y1={y(t)} y2={y(t)} stroke="rgb(var(--fg) / 0.1)" strokeWidth="1" />
            <text x={PL - 8} y={y(t) + 3.5} textAnchor="end" fontSize="11" fill="rgb(var(--subtle))" fontFamily="var(--font-mono)">{t ? `${t}K` : '0'}</text>
          </g>
        ))}
        {[1, 8, 15, 22, 31].map(d => (
          <text key={d} x={x(d - 1)} y={H - 6} textAnchor="middle" fontSize="11" fill="rgb(var(--subtle))" fontFamily="var(--font-mono)">Oct {d}</text>
        ))}
        <path d={path('input')} fill="none" stroke="rgb(var(--c1))" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        <path d={path('output')} fill="none" stroke="rgb(var(--c2))" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        {hover != null && h && (
          <g>
            <line x1={x(hover)} x2={x(hover)} y1={PT} y2={H - PB} stroke="rgb(var(--fg) / 0.3)" strokeWidth="1" />
            <circle cx={x(hover)} cy={y(h.input)} r="4" fill="rgb(var(--c1))" stroke="rgb(var(--surface))" strokeWidth="2" />
            <circle cx={x(hover)} cy={y(h.output)} r="4" fill="rgb(var(--c2))" stroke="rgb(var(--surface))" strokeWidth="2" />
          </g>
        )}
      </svg>
      {hover != null && h && (
        <div
          className="pointer-events-none absolute top-2 border bg-surface px-3 py-2 text-xs shadow-lift"
          style={{ left: `${(x(hover) / W) * 100}%`, transform: `translateX(${hover > data.length * 0.65 ? '-110%' : '10%'})` }}
        >
          <p className="font-mono text-subtle">Oct {h.day}</p>
          <p className="mt-1 flex items-center gap-2"><span aria-hidden className="h-2 w-2 rounded-full" style={{ background: 'rgb(var(--c1))' }} />Input <span className="ml-auto pl-4 font-mono">{h.input}K</span></p>
          <p className="flex items-center gap-2"><span aria-hidden className="h-2 w-2 rounded-full" style={{ background: 'rgb(var(--c2))' }} />Output <span className="ml-auto pl-4 font-mono">{h.output}K</span></p>
        </div>
      )}
    </div>
  )
}

/* ---------- Donut: slices with 2px surface gaps ---------- */
export interface Slice { label: string; value: number; tokens: number }

export function Donut({ slices, centerValue, centerLabel }: { slices: Slice[]; centerValue: string; centerLabel: string }) {
  const reduce = useReducedMotion()
  const [hover, setHover] = useState<number | null>(null)
  const size = 190, r = 70, sw = 26, c = size / 2, circ = 2 * Math.PI * r
  const total = slices.reduce((n, s) => n + s.value, 0)
  const arcs = useMemo(() => {
    return slices.reduce<{ arcs: { len: number; o: number }[]; acc: number }>(
      (accState, s) => {
        const len = total > 0 ? (s.value / total) * circ : 0
        accState.arcs.push({ len, o: accState.acc })
        accState.acc += len
        return accState
      },
      { arcs: [], acc: 0 }
    ).arcs
  }, [slices, total, circ])
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Token usage breakdown: ${slices.map(s => `${s.label} ${s.value}%`).join(', ')}`}>
          <g transform={`rotate(-90 ${c} ${c})`}>
            {slices.map((s, i) => (
              <motion.circle
                key={s.label} cx={c} cy={c} r={r} fill="none" strokeWidth={hover === i ? sw + 4 : sw}
                stroke={`rgb(var(--c${i + 1}))`}
                strokeDasharray={`${Math.max(0, arcs[i].len - 2)} ${circ}`} strokeDashoffset={-arcs[i].o}
                initial={reduce ? false : { opacity: 0 }} animate={{ opacity: hover == null || hover === i ? 1 : 0.45 }}
                transition={{ duration: 0.2 }}
                onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)}
              />
            ))}
          </g>
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="font-display text-2xl font-bold tabular-nums">{hover != null ? `${slices[hover].value}%` : centerValue}</span>
          <span className="max-w-[6rem] text-[0.6875rem] leading-tight text-subtle">{hover != null ? slices[hover].label : centerLabel}</span>
        </div>
      </div>
      <ul className="w-full text-sm">
        {slices.map((s, i) => (
          <li key={s.label} className="flex items-center gap-3 border-b py-2 last:border-b-0" onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)}>
            <span aria-hidden className="h-2.5 w-2.5 shrink-0 rounded-[2px]" style={{ background: `rgb(var(--c${i + 1}))` }} />
            <span className="flex-1">{s.label}</span>
            <span className="font-mono tabular-nums text-subtle">{s.tokens.toLocaleString('en-US')}</span>
            <span className="w-10 text-right font-mono tabular-nums">{s.value}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
