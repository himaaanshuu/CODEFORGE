/**
 * Local heuristic prompt scorer — not a model call.
 *
 * Checks are weighted (objective and specificity matter most); token
 * estimates include a fixed agent-run overhead (system prompt + workspace
 * context) plus ~4 characters per prompt token, so the budget bar in
 * Prompt Lab reflects a realistic request size.
 */
export interface PromptCheck {
  id: string
  label: string
  pass: boolean
  hint: string
  weight: number
}
export interface PromptReport {
  score: number
  checks: PromptCheck[]
  estTokens: number
  estCost: number
}

/** Tokens of system prompt + workspace context sent with every agent run. */
const RUN_OVERHEAD_TOKENS = 3500
/** Blended estimate at ~$3 per 1M tokens. */
const COST_PER_TOKEN = 0.000003

const has = (t: string, re: RegExp) => re.test(t.toLowerCase())
const words = (t: string) => (t.trim() ? t.trim().split(/\s+/).length : 0)

export function scorePrompt(text: string): PromptReport {
  const t = text.trim()
  const checks: PromptCheck[] = [
    {
      id: 'objective',
      label: 'Clear objective',
      weight: 25,
      pass:
        t.length >= 20 &&
        has(t, /\b(add|fix|implement|refactor|update|create|remove|delete|migrate|write|improve|rename|enable|disable|support)\b/),
      hint: 'Start with a verb and say what should change, e.g. “Add rate limiting to …”.',
    },
    {
      id: 'functionality',
      label: 'Specific functionality',
      weight: 25,
      pass:
        words(t) >= 6 &&
        has(t, /\b(endpoint|route|token|login|flow|function|class|api|validation|auth|jwt|handler|model|component|hook|table|schema|query|button|form|agent|workspace|repo|clone|score|prompt|file|middleware|service|view|screen)\b/),
      hint: 'Name the exact feature, endpoint, function or component involved.',
    },
    {
      id: 'context',
      label: 'Relevant context',
      weight: 15,
      pass:
        has(t, /\b(existing|current|fastapi|django|flask|react|vue|node|module|service|app\/|src\/|backend\/|frontend\/)\b/) ||
        /[\w-]+\.(py|ts|tsx|js|jsx|sql|css|md)\b/.test(t),
      hint: 'Mention the framework, a file path, or the existing behaviour this builds on.',
    },
    {
      id: 'constraints',
      label: 'Constraints defined',
      weight: 15,
      pass: has(t, /\b(preserve|keep|without|do not|don.t|must|only|avoid|backwards?|compatible|unchanged|should not)\b/),
      hint: 'State what must not break, e.g. preserve the current response shape.',
    },
    {
      id: 'testable',
      label: 'Testable outcome',
      weight: 20,
      pass: has(t, /\b(tests?|coverage|return|returns|status codes?|401|403|404|200|assert|should|expect|verify|ensure)\b/),
      hint: 'Say how success is checked — tests, status codes, or expected behaviour.',
    },
  ]
  const base = checks.reduce((sum, c) => sum + (c.pass ? c.weight : 0), 0)
  const lengthBonus = t ? Math.min(5, Math.floor(t.length / 80)) : 0
  const score = t ? Math.min(100, base + lengthBonus) : 0
  const promptTokens = t ? Math.max(1, Math.round(t.length / 4)) : 0
  const estTokens = promptTokens ? RUN_OVERHEAD_TOKENS + promptTokens : 0
  return { score, checks, estTokens, estCost: estTokens * COST_PER_TOKEN }
}

export function improvePrompt(text: string, report: PromptReport): string {
  const base = text.trim().replace(/[.\s]+$/, '')
  const add: string[] = []
  const miss = (id: string) => report.checks.find(c => c.id === id && !c.pass)
  if (miss('functionality')) add.push('Target the specific endpoint, function or file involved')
  if (miss('context')) add.push('Work within the existing project structure')
  if (miss('constraints')) add.push('Preserve current behaviour and do not modify unrelated modules')
  if (miss('testable')) add.push('Add tests and return clear status codes for invalid input')
  const lead = miss('objective') ? `Implement the following change: ${base}` : base
  return add.length ? `${lead}. ${add.join('. ')}.` : `${lead}.`
}
