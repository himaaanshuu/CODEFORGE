import { motion, useReducedMotion } from 'framer-motion'
import { BookOpen, Check, FlaskConical, Hammer, ListChecks, Search, ShieldCheck, Wrench, type LucideIcon } from 'lucide-react'
import { Brand } from '../components/ui/Brand'
import { Button } from '../components/ui/Button'
import { ThemeToggle } from '../components/ui/ThemeToggle'
import type { Theme } from '../hooks/useTheme'

interface Props { theme: Theme; onToggleTheme: () => void; onStart: () => void; onDocs: () => void }

type Tone = 'bad' | 'ok'
const pipeline: { label: string; note: string; icon: LucideIcon; tone?: Tone }[] = [
  { label: 'Understand', note: 'Reads your task and the codebase', icon: BookOpen },
  { label: 'Explore', note: 'Finds the files that matter', icon: Search },
  { label: 'Plan', note: 'Decides what to change', icon: ListChecks },
  { label: 'Build', note: 'Writes the implementation', icon: Hammer },
  { label: 'Test', note: 'Runs your test suite', icon: FlaskConical, tone: 'bad' },
  { label: 'Repair', note: 'Fixes what failed', icon: Wrench, tone: 'bad' },
  { label: 'Verify', note: 'Confirms everything passes', icon: ShieldCheck, tone: 'ok' },
]

const features = [
  { kicker: '01', title: 'Understands your repository', body: 'Maps modules, routes and dependencies before touching a line.' },
  { kicker: '02', title: 'Proves its own work', body: 'Every change is run against your tests, not just written.' },
  { kicker: '03', title: 'Repairs, then reports', body: 'Failures are analysed and fixed; you see the full trail.' },
]

const plans = [
  {
    name: 'Free',
    price: '0',
    blurb: 'Try the agent on your first repository.',
    features: ['25 agent runs / month', '1 connected repository', 'Nano model', 'Prompt scoring', '7-day run history', 'Community support'],
    cta: 'Get started',
    featured: false,
  },
  {
    name: 'Basic',
    price: '12',
    blurb: 'For side projects that need real repairs.',
    features: ['150 agent runs / month', '5 connected repositories', 'Standard model', 'Diffs & sandboxed tests', '30-day run history', 'Email support'],
    cta: 'Start Basic',
    featured: false,
  },
  {
    name: 'Pro',
    price: '29',
    blurb: 'For daily shipping with the full loop.',
    features: ['1,000 agent runs / month', 'Unlimited repositories', 'Super model', 'Priority execution', 'Usage & efficiency analytics', '90-day run history'],
    cta: 'Start Pro',
    featured: true,
  },
  {
    name: 'Elite',
    price: '79',
    blurb: 'For teams and power users at full throttle.',
    features: ['Unlimited agent runs', 'Early-access features', '3 team seats', 'Custom model configuration', 'Dedicated support', 'Priority response SLA'],
    cta: 'Start Elite',
    featured: false,
  },
]

const toneIcon = (t?: Tone) => (t === 'bad' ? 'bg-bad/12 text-bad' : t === 'ok' ? 'bg-ok/12 text-ok' : 'bg-accent/12 text-accent')

export function Landing({ theme, onToggleTheme, onStart, onDocs }: Props) {
  const reduce = useReducedMotion()
  const rise = (i: number) =>
    reduce ? {} : {
      initial: { opacity: 0, y: 16 }, animate: { opacity: 1, y: 0 },
      transition: { delay: 0.07 * i, duration: 0.55, ease: [0.22, 1, 0.36, 1] as const },
    }

  return (
    <div className="min-h-screen bg-bg">
      <header className="sticky top-0 z-20 border-b bg-bg/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-3.5">
          <Brand />
          <nav aria-label="Primary" className="hidden items-center gap-7 text-sm text-subtle md:flex">
            <a href="#features" className="transition-colors duration-fast hover:text-fg">Features</a>
            <a href="#how" className="transition-colors duration-fast hover:text-fg">How it works</a>
            <a href="#pricing" className="transition-colors duration-fast hover:text-fg">Pricing</a>
            <button type="button" onClick={onDocs} className="transition-colors duration-fast hover:text-fg">Docs</button>
          </nav>
          <div className="flex items-center gap-2">
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <span className="hidden sm:block"><Button variant="ghost" size="sm" onClick={onStart}>Sign in</Button></span>
            <Button size="sm" onClick={onStart}>Sign up</Button>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div aria-hidden className="dot-grid pointer-events-none absolute inset-0 opacity-70" />
          <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 pb-20 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:pt-20">
            <div>
              <motion.p {...rise(0)} className="chip">Autonomous software engineering</motion.p>
              <motion.h1
                {...rise(1)}
                className="mt-6 font-display text-[clamp(2.6rem,7vw,4.6rem)] font-bold leading-[0.95] tracking-tight"
              >
                Build software.
                <span className="mt-1 block text-accent">Prove it works.</span>
              </motion.h1>
              <motion.p {...rise(2)} className="mt-6 max-w-lg text-[0.975rem] leading-relaxed text-subtle">
                An autonomous agent that understands your repository, implements your requirements,
                tests its changes, repairs failures, and verifies the result.
              </motion.p>
              <motion.div {...rise(3)} className="mt-8 flex flex-wrap gap-3">
                <Button onClick={onStart}>Get started</Button>
                <a
                  href="#how"
                  className="inline-flex items-center justify-center whitespace-nowrap rounded-sm border border-strong bg-surface px-5 py-2.5 font-display text-xs font-semibold tracking-[0.1em] transition-colors duration-fast hover:bg-raised"
                >
                  See how it works
                </a>
              </motion.div>
              <motion.dl {...rise(4)} className="mt-10 grid max-w-md grid-cols-3 gap-4">
                {[
                  ['7', 'stages'],
                  ['Tests', 'first'],
                  ['Repair', 'loop'],
                ].map(([value, label]) => (
                  <div key={label} className="rounded-sm border bg-surface/80 px-3 py-3">
                    <dt className="font-display text-lg font-bold leading-none">{value}</dt>
                    <dd className="mt-1 text-[11px] uppercase tracking-[0.12em] text-subtle">{label}</dd>
                  </div>
                ))}
              </motion.dl>
            </div>

            <motion.aside
              {...rise(2)}
              aria-hidden
              className="panel relative overflow-hidden p-0"
            >
              <div className="flex items-center justify-between border-b bg-raised px-4 py-2.5">
                <span className="font-mono text-[11px] text-subtle">forge — agent</span>
                <span className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-bad/70" />
                  <span className="h-2 w-2 rounded-full bg-rust/80" />
                  <span className="h-2 w-2 rounded-full bg-ok/80" />
                </span>
              </div>
              <div className="space-y-3 p-5 font-mono text-[12px] leading-relaxed">
                <p className="text-subtle">$ forge run — “Add JWT auth to /login”</p>
                <p className="text-info">→ exploring app/auth · 14 files</p>
                <p className="text-fg">→ plan: protect routes, keep login shape</p>
                <p className="text-ok">✓ 84 tests passing</p>
                <p className="text-ok">✓ repair verified · patch applied</p>
                <div className="mt-4 rounded-sm border bg-bg p-3">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-subtle">Verification</p>
                  <p className="mt-1 font-display text-lg font-bold tracking-tight text-ok">Completed</p>
                  <p className="mt-1 text-[11px] text-subtle">Files changed 3 · Repair attempts 1</p>
                </div>
              </div>
            </motion.aside>
          </div>
        </section>

        <section id="how" aria-labelledby="how-h" className="border-t bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <p className="eyebrow text-center">Pipeline</p>
            <h2 id="how-h" className="mt-2 text-center font-display text-3xl font-bold tracking-tight">How it works</h2>
            <ol className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
              {pipeline.map(({ label, note, icon: Icon, tone }, i) => (
                <motion.li
                  key={label}
                  initial={reduce ? false : { opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: reduce ? 0 : 0.06 * i, duration: 0.4 }}
                  className="rounded-md border bg-bg p-4"
                >
                  <span className={`flex h-9 w-9 items-center justify-center rounded-full ${toneIcon(tone)}`}>
                    <Icon size={16} aria-hidden />
                  </span>
                  <p className="mt-3 font-display text-sm font-semibold">{label}</p>
                  <p className="mt-1 text-xs leading-snug text-subtle">{note}</p>
                </motion.li>
              ))}
            </ol>
          </div>
        </section>

        <section id="features" aria-label="Features" className="border-t">
          <ul className="mx-auto grid max-w-6xl gap-4 px-6 py-16 md:grid-cols-3">
            {features.map((f, i) => (
              <motion.li
                key={f.title}
                initial={reduce ? false : { opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: reduce ? 0 : 0.08 * i, duration: 0.45 }}
                className="panel p-6"
              >
                <p className="font-mono text-[11px] text-accent">{f.kicker}</p>
                <h3 className="mt-3 font-display text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-subtle">{f.body}</p>
              </motion.li>
            ))}
          </ul>
        </section>

        <section id="pricing" aria-labelledby="pricing-h" className="border-t bg-surface">
          <div className="mx-auto max-w-6xl px-6 py-16">
            <p className="eyebrow text-center">Pricing</p>
            <h2 id="pricing-h" className="mt-2 text-center font-display text-3xl font-bold tracking-tight">Simple plans, serious agent</h2>
            <p className="mx-auto mt-3 max-w-md text-center text-sm leading-relaxed text-subtle">
              Every plan includes the full plan → edit → test → repair → verify loop. Pick the throughput you need.
            </p>
            <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {plans.map((p, i) => (
                <motion.li
                  key={p.name}
                  initial={reduce ? false : { opacity: 0, y: 10 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: reduce ? 0 : 0.06 * i, duration: 0.4 }}
                  className={`panel relative flex flex-col p-6 ${p.featured ? 'border-accent' : ''}`}
                >
                  {p.featured && (
                    <span className="absolute -top-2.5 left-6 rounded-full bg-accent px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-on-accent">
                      Most popular
                    </span>
                  )}
                  <p className="eyebrow">{p.name}</p>
                  <p className="mt-3 flex items-baseline gap-1">
                    <span className="font-display text-4xl font-bold tracking-tight">${p.price}</span>
                    <span className="font-mono text-xs text-subtle">/mo</span>
                  </p>
                  <p className="mt-2 text-sm leading-relaxed text-subtle">{p.blurb}</p>
                  <ul className="mt-5 flex-1 space-y-2">
                    {p.features.map(f => (
                      <li key={f} className="flex items-start gap-2.5 text-sm">
                        <Check size={14} className="mt-0.5 shrink-0 text-ok" aria-hidden />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-6">
                    <Button full size="sm" onClick={onStart} variant={p.featured ? 'primary' : 'ghost'}>{p.cta}</Button>
                  </div>
                </motion.li>
              ))}
            </ul>
            <p className="mt-6 text-center font-mono text-[11px] text-subtle">
              Prices in USD, billed monthly · cancel anytime
            </p>
          </div>
        </section>
      </main>
    </div>
  )
}
