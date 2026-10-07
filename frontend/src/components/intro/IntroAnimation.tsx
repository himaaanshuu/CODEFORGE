import { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'

const TITLE = 'CODEFORGE AI'
const TAG = 'AUTONOMOUS SOFTWARE ENGINEERING'

/** ~1.5s: typed wordmark, then tagline, then onDone. Runs once per page load. */
export function IntroAnimation({ onDone }: { onDone: () => void }) {
  const reduce = useReducedMotion()
  const [count, setCount] = useState(reduce ? TITLE.length : 0)
  const [showTag, setShowTag] = useState(!!reduce)

  useEffect(() => {
    const timers: number[] = []
    if (reduce) {
      timers.push(window.setTimeout(onDone, 350))
    } else {
      const step = 55
      for (let i = 1; i <= TITLE.length; i++) timers.push(window.setTimeout(() => setCount(i), 120 + i * step))
      const typed = 120 + TITLE.length * step
      timers.push(window.setTimeout(() => setShowTag(true), typed + 60))
      timers.push(window.setTimeout(onDone, typed + 620))
    }
    return () => timers.forEach(window.clearTimeout)
  }, [reduce, onDone])

  return (
    <motion.div
      className="on-ink fixed inset-0 z-50 flex flex-col items-center justify-center bg-ink px-6 text-cream"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: reduce ? 0.1 : 0.4, ease: [0.22, 1, 0.36, 1] }}
      role="status"
      aria-label="Loading CodeForge AI"
    >
      <h1 className="font-display text-[clamp(1.75rem,6vw,3.25rem)] font-bold tracking-[0.18em]" aria-label={TITLE}>
        <span aria-hidden="true">
          {TITLE.slice(0, count)}
          <span className="ml-1 inline-block h-[0.85em] w-[3px] translate-y-[0.1em] bg-burgundy-light" />
        </span>
      </h1>
      <motion.p
        className="mt-5 font-display text-[0.6875rem] font-medium tracking-[0.32em] text-cream-muted"
        initial={{ opacity: 0, y: 6 }}
        animate={showTag ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
        transition={{ duration: 0.3 }}
      >
        {TAG}
      </motion.p>
    </motion.div>
  )
}
