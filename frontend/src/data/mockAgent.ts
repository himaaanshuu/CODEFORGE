/**
 * MOCK DATA LAYER — no backend is called here.
 * Swap `startMockRun` for a client against POST /api/v1/agent/analyze
 * (and future agent endpoints) keeping the same `AgentRun` / `AgentClient` shapes.
 */
import type { ActivityEvent, AgentRun, FileChange, Repository, TestRun, DiffLine } from '../types'

export const mockRepository: Repository = {
  name: 'codeforge-demo',
  owner: 'acme',
  branch: 'main',
  language: 'TypeScript',
  files: 11,
  description: 'Demo service with JWT session handling, a typed API client and an auth test suite.',
  tree: [
    {
      name: 'src', path: 'src', type: 'dir',
      children: [
        {
          name: 'auth', path: 'src/auth', type: 'dir',
          children: [
            { name: 'session.ts', path: 'src/auth/session.ts', type: 'file' },
            { name: 'login.ts', path: 'src/auth/login.ts', type: 'file' },
          ],
        },
        {
          name: 'services', path: 'src/services', type: 'dir',
          children: [{ name: 'api.ts', path: 'src/services/api.ts', type: 'file' }],
        },
        { name: 'app.ts', path: 'src/app.ts', type: 'file' },
      ],
    },
    {
      name: 'tests', path: 'tests', type: 'dir',
      children: [{ name: 'auth.test.ts', path: 'tests/auth.test.ts', type: 'file' }],
    },
    { name: 'package.json', path: 'package.json', type: 'file' },
    { name: 'README.md', path: 'README.md', type: 'file' },
  ],
}

const ctx = (n: number, text: string): DiffLine => ({ kind: 'context', oldNo: n, newNo: n, text })

const sessionLines: DiffLine[] = [
  ctx(38, 'export async function getSession(token: string): Promise<Session> {'),
  ctx(39, '  const claims = decode(token)'),
  ctx(40, ''),
  { kind: 'del', oldNo: 41, text: '  if (claims.exp < Date.now() / 1000) {' },
  { kind: 'del', oldNo: 42, text: '    throw new AuthError("token expired")' },
  { kind: 'del', oldNo: 43, text: '  }' },
  { kind: 'add', newNo: 41, text: '  if (isExpired(claims)) {' },
  { kind: 'add', newNo: 42, text: '    const refreshed = await refreshExpiredToken(token)' },
  { kind: 'add', newNo: 43, text: '    return buildSession(refreshed)' },
  { kind: 'add', newNo: 44, text: '  }' },
  ctx(44, ''),
  { kind: 'del', oldNo: 45, text: '  return validate(token)' },
  { kind: 'add', newNo: 46, text: '  return buildSession(token)' },
  ctx(46, '}'),
]

const loginLines: DiffLine[] = [
  ctx(12, 'export async function login(creds: Credentials) {'),
  { kind: 'del', oldNo: 13, text: '  const { token } = await api.post("/login", creds)' },
  { kind: 'add', newNo: 13, text: '  const { token, refreshToken } = await api.post("/login", creds)' },
  { kind: 'add', newNo: 14, text: '  storeRefreshToken(refreshToken)' },
  ctx(14, '  return getSession(token)'),
  ctx(15, '}'),
]

const testLines: DiffLine[] = [
  ctx(20, 'describe("session", () => {'),
  { kind: 'add', newNo: 21, text: '  it("refreshes an expired token instead of throwing", async () => {' },
  { kind: 'add', newNo: 22, text: '    const expired = signToken({ exp: nowSeconds() - 60 })' },
  { kind: 'add', newNo: 23, text: '    const session = await getSession(expired)' },
  { kind: 'add', newNo: 24, text: '    expect(session.isExpired).toBe(false)' },
  { kind: 'add', newNo: 25, text: '  })' },
  ctx(26, '})'),
]

export const mockChanges: FileChange[] = [
  { path: 'src/auth/session.ts', added: 12, removed: 4, lines: sessionLines },
  { path: 'src/auth/login.ts', added: 8, removed: 2, lines: loginLines },
  { path: 'tests/auth.test.ts', added: 27, removed: 0, lines: testLines },
]

export const mockTests: TestRun = {
  suites: [
    { name: 'Authentication tests', passed: 18, failed: 0 },
    { name: 'API tests', passed: 14, failed: 0 },
    { name: 'Integration tests', passed: 10, failed: 0 },
  ],
  durationSeconds: 4.82,
}

/** Source text shown in the plain code viewer (post-change), keyed by path. */
export const mockSources: Record<string, string> = {
  'src/auth/session.ts': sessionLines.filter(l => l.kind !== 'del').map(l => l.text).join('\n'),
  'src/auth/login.ts': loginLines.filter(l => l.kind !== 'del').map(l => l.text).join('\n'),
  'tests/auth.test.ts': testLines.filter(l => l.kind !== 'del').map(l => l.text).join('\n'),
  'src/services/api.ts': 'export const api = {\n  async post(path: string, body: unknown) {\n    const res = await fetch(BASE_URL + path, {\n      method: "POST",\n      body: JSON.stringify(body),\n    })\n    return res.json()\n  },\n}',
  'src/app.ts': 'import { api } from "./services/api"\nimport { login } from "./auth/login"\n\nexport async function start() {\n  // bootstrap the service\n  return { api, login }\n}',
  'package.json': '{\n  "name": "codeforge-demo",\n  "version": "1.4.0",\n  "scripts": { "test": "vitest run" }\n}',
  'README.md': '# codeforge-demo\n\nDemo service with JWT session handling.',
}

const script: Omit<ActivityEvent, 'id' | 'time'>[] = [
  { text: 'Repository analyzed', state: 'READY', status: 'done' },
  { text: 'Understanding coding task', state: 'ANALYZING', status: 'done' },
  { text: 'Exploring repository structure', state: 'EXPLORING', status: 'done' },
  { text: 'Planning implementation', state: 'PLANNING', status: 'done' },
  { text: 'Modifying code', state: 'MODIFICATION', status: 'done' },
  { text: 'Running test suite', state: 'TESTING', status: 'done' },
  { text: '2 tests failed', state: 'FAILURE_ANALYSIS', status: 'done' },
  { text: 'Repair attempt 1 of 5', state: 'REPAIR', status: 'done' },
  { text: 'Diagnosing test failure', state: 'FAILURE_ANALYSIS', status: 'done' },
  { text: 'Applying targeted patch', state: 'REPAIR', status: 'done' },
  { text: 'Running tests again', state: 'TESTING', status: 'done' },
  { text: '31 tests passed', state: 'VERIFICATION', status: 'done' },
  { text: 'Verification complete', state: 'COMPLETED', status: 'done' },
]

export interface RunHandlers {
  onEvent: (e: ActivityEvent) => void
  onComplete: (r: AgentRun) => void
}

const pad = (n: number) => String(n).padStart(2, '0')
const formatTime = (d: Date) => `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
const clock = (_d: Date) => formatTime(new Date())

/** Simulates a run with timers. Returns a cancel function. */
export function startMockRun(_task: string, handlers: RunHandlers, stepMs = 1100): () => void {
  const timers: number[] = []
  const events: ActivityEvent[] = []
  script.forEach((step, i) => {
    timers.push(window.setTimeout(() => {
      const ev: ActivityEvent = { ...step, id: `ev-${i}`, time: clock(new Date()) }
      events.push(ev)
      handlers.onEvent(ev)
      if (i === script.length - 1) {
        handlers.onComplete({
          events,
          changes: mockChanges,
          tests: mockTests,
          result: { summary: 'Authentication refresh flow updated.', filesChanged: 3, testsPassed: 42, regressions: 0 },
          repairAttempts: 0,
          verification: {
            targetIssueResolved: true,
            regressionSuitePassed: true,
            changesValidated: true,
          },
        })
      }
    }, 400 + i * stepMs))
  })
  return () => timers.forEach(t => window.clearTimeout(t))
}