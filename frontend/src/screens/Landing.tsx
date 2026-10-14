import { motion, useReducedMotion } from 'framer-motion'
import { BookOpen, FlaskConical, Hammer, ListChecks, Search, ShieldCheck, Wrench, type LucideIcon } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { Logo } from '../components/ui/Logo'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import type { Theme } from '../hooks/useTheme'

interface Props { theme: Theme; onToggleTheme: () => void; onStart: () => void }

type Tone = 'bad' | 'ok'
const pipeline: { label: string; note: string; icon: LucideIcon; tone?: Tone }[] = [
  { label: 'UNDERSTAND', note: 'Reads your task and the codebase', icon: BookOpen },
  { label: 'EXPLORE', note: 'Finds the files that matter', icon: Search },
  { label: 'PLAN', note: 'Decides what to change', icon: ListChecks },
  { label: 'BUILD', note: 'Writes the implementation', icon: Hammer },
  { label: 'TEST', note: 'Runs your test suite', icon: FlaskConical, tone: 'bad' },
  { label: 'REPAIR', note: 'Fixes what failed', icon: Wrench, tone: 'bad' },
  { label: 'VERIFY', note: 'Confirms everything passes', icon: ShieldCheck, tone: 'ok' },
]

const features = [
  { title: 'Understands your repository', body: 'Maps modules, routes and dependencies before touching a line.' },
  { title: 'Proves its own work', body: 'Every change is run against your tests, not just written.' },
  { title: 'Repairs, then reports', body: 'Failures are analysed and fixed; you see the full trail.' },
]

const toneText = (t?: Tone) => (t === 'bad' ? 'text-bad' : t === 'ok' ? 'text-ok' : 'text-subtle')
const toneRing = (t?: Tone) => (t === 'bad' ? 'border-bad text-bad' : t === 'ok' ? 'border-ok text-ok' : 'border-strong text-fg')

export function Landing({ theme, onToggleTheme, onStart }: Props) {
  const reduce = useReducedMotion()
  const rise = (i: number) =>
    reduce ? {} : {
      initial: { opacity: 0, y: 14 }, animate: { opacity: 1, y: 0 },
      transition: { delay: 0.08 * i, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
    }

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-5">
        <Logo className="text-[0.9375rem]" />
        <nav aria-label="Primary" className="hidden items-center gap-7 text-sm text-subtle md:flex">
          <a href="#features" className="transition-colors duration-fast hover:text-fg">Features</a>
          <a href="#how" className="transition-colors duration-fast hover:text-fg">How it works</a>
          <span title="Coming soon" aria-disabled="true" className="cursor-default opacity-60">Pricing</span>
          <span title="Coming soon" aria-disabled="true" className="cursor-default opacity-60">Docs</span>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          <span className="hidden sm:block"><Button variant="ghost" size="sm" onClick={onStart}>SIGN IN</Button></span>
          <Button size="sm" onClick={onStart}>SIGN UP</Button>
        </div>
      </header>

      <main>
        {/* HERO — centered, no side card */}
        <section className="mx-auto max-w-4xl px-6 pb-16 pt-14 text-center md:pt-24">
          <motion.p {...rise(0)} className="eyebrow">Autonomous software engineering</motion.p>
          <motion.h1
            {...rise(1)}
            className="mt-5 font-display text-[clamp(3rem,10vw,7rem)] font-bold leading-[0.92] tracking-tight text-accent"
          >
            CODEFORGE <span className="text-fg">AI</span>
          </motion.h1>
          <motion.p {...rise(2)} className="mx-auto mt-8 max-w-2xl font-display text-[clamp(1.4rem,3.2vw,2.1rem)] font-medium leading-snug">
            Build software.<br />Let CodeForge prove it works.
          </motion.p>
          <motion.p {...rise(3)} className="mx-auto mt-5 max-w-xl text-[0.9375rem] text-subtle">
            An autonomous agent that understands your repository, implements your requirements,
            tests its changes, repairs failures, and verifies the result.
          </motion.p>
          <motion.div {...rise(4)} className="mt-9 flex flex-wrap justify-center gap-3">
            <Button onClick={onStart}>GET STARTED</Button>
            <a
              href="#how"
              className="inline-flex items-center justify-center whitespace-nowrap rounded-sm border border-strong px-5 py-2.5 font-display text-xs font-semibold tracking-[0.12em] transition-colors duration-fast hover:bg-raised"
            >
              SEE HOW IT WORKS
            </a>
          </motion.div>
        </section>

        {/* PIPELINE — the focal visual; line fills, steps light up in sequence */}
        <section id="how" aria-labelledby="how-h" className="mx-auto max-w-6xl px-6 pb-20">
          <h2 id="how-h" className="eyebrow mb-10 text-center">How it works</h2>
          <ol className="relative grid grid-cols-2 gap-x-4 gap-y-10 sm:grid-cols-4 lg:grid-cols-7">
            <span aria-hidden className="absolute left-[7%] right-[7%] top-[22px] hidden h-px bg-[color:var(--line)] lg:block" />
            <motion.span
              aria-hidden
              className="absolute left-[7%] right-[7%] top-[22px] hidden h-px origin-left bg-accent lg:block"
              initial={reduce ? false : { scaleX: 0 }} whileInView={{ scaleX: 1 }} viewport={{ once: true }}
              transition={{ duration: 1.4, ease: [0.22, 1, 0.36, 1] }}
            />
            {pipeline.map(({ label, note, icon: Icon, tone }, i) => (
              <motion.li
                key={label}
                initial={reduce ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: reduce ? 0 : 0.12 * i, duration: 0.45 }}
                className="relative flex flex-col items-center text-center"
              >
                <span className={`flex h-11 w-11 items-center justify-center rounded-full border bg-bg ${toneRing(tone)}`}>
                  <Icon size={18} aria-hidden />
                </span>
                <span className={`mt-4 font-display text-[0.6875rem] font-semibold tracking-[0.16em] ${tone ? toneText(tone) : 'text-fg'}`}>{label}</span>
                <span className="mt-1.5 max-w-[10rem] text-xs leading-snug text-subtle">{note}</span>
              </motion.li>
            ))}
          </ol>
        </section>

        {/* FEATURES — open columns, no cards */}
        <section id="features" aria-label="Features" className="border-t">
          <ul className="mx-auto grid max-w-6xl gap-10 px-6 py-16 md:grid-cols-3">
            {features.map((f, i) => (
              <motion.li
                key={f.title}
                initial={reduce ? false : { opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: reduce ? 0 : 0.1 * i, duration: 0.45 }}
                className="border-l-2 border-accent pl-5"
              >
                <h3 className="font-display text-base font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-subtle">{f.body}</p>
              </motion.li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  )
}
