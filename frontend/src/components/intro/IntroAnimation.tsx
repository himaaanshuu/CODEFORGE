import { useEffect, useState } from 'react'

const TITLE = 'CODEFORGE AI'

export function IntroAnimation({ onDone }: { onDone: () => void }) {
  const [showTag, setShowTag] = useState(false)

  useEffect(() => {
    const tagTimeout = setTimeout(() => setShowTag(true), 520)
    const doneTimeout = setTimeout(onDone, 720)
    return () => {
      clearTimeout(tagTimeout)
      clearTimeout(doneTimeout)
    }
  }, [onDone])

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-ink px-6 text-cream">
      <h1 className="font-display text-[clamp(1.75rem,6vw,3.25rem)] font-bold tracking-tight">{TITLE}</h1>
      {showTag && <p className="mt-4 text-subtle">AUTONOMOUS SOFTWARE ENGINEERING</p>}
    </div>
  )
}