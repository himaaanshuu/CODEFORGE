/**
 * Agent Client — real backend API client for CodeForge AI.
 *
 * Talks to the FastAPI backend (default http://localhost:8000) and maps
 * responses onto the frontend's display types. No mock data lives here.
 */

import type {
  ActivityEvent,
  AgentRunView,
  AgentState,
  DiffLine,
  FileChange,
  RepoNode,
  WorkspaceInfo,
} from '../types'
import { getCurrentAccessToken } from './supabase'

let rawBase: string = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'
rawBase = rawBase.replace(/\/$/, '')
if (rawBase.endsWith('/api')) {
  rawBase = `${rawBase}/v1`
}
export const API_BASE = rawBase
const HEALTH_URL = `${API_BASE.replace(/\/api(\/v1)?\/?$/, '')}/health`

/** JSON headers with a Supabase access token when somebody is signed in. */
async function authedHeaders(extra: Record<string, string> = {}): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra }
  const token = await getCurrentAccessToken()
  if (token) headers.Authorization = `Bearer ${token}`
  return headers
}

/** True when the backend rejected the request because of authentication. */
function isAuthFailure(status: number): boolean {
  return status === 401 || status === 503
}

// --- Response shapes of the real backend ---------------------------------

interface AnalysisObservation {
  tool_name: string
  tool_success: boolean
  observation: string
  raw_data?: Record<string, unknown> | null
}

interface AnalysisResponse {
  success: boolean
  status: string
  summary: string
  files_inspected: string[]
  tools_used: string[]
  plan: string[]
  observations: AnalysisObservation[]
  error: string | null
  iteration: number
  duration_seconds?: number
  tokens_used?: number
  model?: string
  files_changed?: string[]
  diff_summary?: string
  repair_attempts?: number
  max_iterations?: number
  phase?: string
}

export interface FilePayload {
  path: string
  content: string
  truncated: boolean
  bytes: number
}

export interface PublishChangesResult {
  branch: string
  commit: string
  repository: string
  url: string
  message: string
}

/** Display label → Nebius model ID for the agent model picker. */
export const MODEL_IDS: Record<string, string> = {
  'Nemotron 3 Ultra': 'nvidia/Nemotron-3-Ultra-550b-a55b',
  'Nemotron 3 Super': 'nvidia/nemotron-3-super-120b-a12b',
  'Nemotron 3 Nano': 'nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B',
}

/** Map a picker label (or a raw model ID) to the ID sent to the backend. */
export function modelForLabel(label: string): string {
  return MODEL_IDS[label] ?? label
}

// --- Helpers --------------------------------------------------------------

const TOOL_STATE: Record<string, AgentState> = {
  list_files: 'SEARCHING',
  read_file: 'READING',
  search_code: 'SEARCHING',
  apply_patch: 'IMPLEMENTING',
  write_file: 'IMPLEMENTING',
  inspect_diff: 'IMPLEMENTING',
  run_tests: 'TESTING',
}

function clock(offsetMs = 0): string {
  return new Date(Date.now() + offsetMs).toLocaleTimeString('en-GB', { hour12: false })
}

function clip(text: string, max = 240): string {
  const t = (text || '').replace(/\s+/g, ' ').trim()
  return t.length > max ? `${t.slice(0, max - 1)}…` : t
}

/** Parse a unified diff into per-file changes the diff viewer can render. */
export function parseUnifiedDiff(diff: string): FileChange[] {
  const files: FileChange[] = []
  let cur: FileChange | null = null
  let oldNo = 0
  let newNo = 0

  for (const raw of (diff || '').split(/\r?\n/)) {
    if (raw.startsWith('diff --git ')) {
      cur = null
      continue
    }
    if (raw.startsWith('--- ')) continue
    if (raw.startsWith('+++ ')) {
      let p = raw.slice(4).trim()
      if (p.startsWith('b/')) p = p.slice(2)
      if (p === '/dev/null') {
        cur = null
        continue
      }
      cur = { path: p, added: 0, removed: 0, lines: [] }
      files.push(cur)
      continue
    }
    const hunk = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/.exec(raw)
    if (hunk) {
      oldNo = parseInt(hunk[1], 10)
      newNo = parseInt(hunk[2], 10)
      continue
    }
    if (!cur) continue
    if (raw.startsWith('+')) {
      const line: DiffLine = { kind: 'add', newNo, text: raw.slice(1) }
      cur.lines.push(line)
      cur.added += 1
      newNo += 1
    } else if (raw.startsWith('-')) {
      const line: DiffLine = { kind: 'del', oldNo, text: raw.slice(1) }
      cur.lines.push(line)
      cur.removed += 1
      oldNo += 1
    } else if (raw.startsWith('\\')) {
      continue
    } else {
      const line: DiffLine = { kind: 'context', oldNo, newNo, text: raw }
      cur.lines.push(line)
      oldNo += 1
      newNo += 1
    }
  }
  return files.filter(f => f.lines.length > 0)
}

function buildEvents(data: AnalysisResponse): ActivityEvent[] {
  const evs: ActivityEvent[] = []
  const push = (text: string, state: AgentState, status: 'done' | 'failed', detail?: string) => {
    evs.push({ id: `ev-${evs.length}`, time: clock(evs.length * 120), text, state, status, detail })
  }

  if (data.plan && data.plan.length > 0) {
    push(`Plan created — ${data.plan.length} steps`, 'PLANNING', 'done', clip(data.plan.join(' → '), 320))
  }
  if (data.files_inspected && data.files_inspected.length > 0) {
    push(`Inspected ${data.files_inspected.length} entries`, 'READING', 'done', clip(data.files_inspected.slice(0, 8).join(', ')))
  }
  for (const obs of data.observations ?? []) {
    push(
      clip(obs.observation) || `${obs.tool_name} finished`,
      TOOL_STATE[obs.tool_name] ?? 'READING',
      obs.tool_success ? 'done' : 'failed',
      `via ${obs.tool_name}`,
    )
  }
  if (data.files_changed && data.files_changed.length > 0) {
    push(`Modified ${data.files_changed.length} file(s)`, 'IMPLEMENTING', 'done', clip(data.files_changed.join(', ')))
  }

  const ok = data.status === 'completed' && !data.error
  if (ok) {
    push(clip(data.summary || 'Analysis completed', 320), 'COMPLETED', 'done')
  } else {
    push(clip(data.error || data.summary || 'Agent run failed', 320), 'FAILED', 'failed')
  }
  return evs
}

function mapAnalysis(data: AnalysisResponse): AgentRunView {
  const changes = parseUnifiedDiff(data.diff_summary ?? '')
  const filesChanged = data.files_changed && data.files_changed.length > 0
    ? data.files_changed
    : changes.map(c => c.path)
  const ok = data.status === 'completed' && !data.error
  const latestTestObservation = [...(data.observations ?? [])]
    .reverse()
    .find(obs => obs.tool_name === 'run_tests' && obs.raw_data)
  const testData = latestTestObservation?.raw_data
  const testSummary = testData?.test_summary as Record<string, unknown> | undefined
  const tests = testData && testSummary
    ? {
        passed: Number(testSummary.passed ?? 0),
        failed: Number(testSummary.failed ?? 0),
        skipped: Number(testSummary.skipped ?? 0),
        errors: Number(testSummary.errors ?? 0),
        durationSeconds: Number(testData.duration_ms ?? 0) / 1000,
        success: Boolean(testData.success),
        exitCode: typeof testData.exit_code === 'number' ? testData.exit_code : null,
        timedOut: Boolean(testData.timed_out),
        output: [testData.stdout, testData.stderr]
          .filter((part): part is string => typeof part === 'string' && part.length > 0)
          .join('\n')
          .slice(0, 20_000),
      }
    : null

  return {
    success: ok,
    status: data.status,
    message: ok ? data.summary : (data.error || data.summary || 'Agent run failed'),
    events: buildEvents(data),
    plan: data.plan ?? [],
    filesInspected: data.files_inspected ?? [],
    filesChanged,
    changes,
    tests,
    metrics: {
      durationSeconds: data.duration_seconds ?? 0,
      tokensUsed: data.tokens_used ?? 0,
      iterations: data.iteration ?? 0,
      maxIterations: data.max_iterations ?? 10,
      toolsUsed: data.tools_used ?? [],
      repairAttempts: data.repair_attempts ?? 0,
      filesChanged: filesChanged.length,
      model: data.model ?? '',
    },
  }
}

function failureRun(task: string, message: string): AgentRunView {
  return {
    success: false,
    status: 'error',
    message,
    events: [
      { id: 'ev-0', time: clock(), text: `Task accepted: ${task}`, state: 'ANALYZING', status: 'done' },
      { id: 'ev-1', time: clock(120), text: clip(message, 320), state: 'FAILED', status: 'failed', detail: 'backend request' },
    ],
    plan: [],
    filesInspected: [],
    filesChanged: [],
    changes: [],
    tests: null,
    metrics: {
      durationSeconds: 0,
      tokensUsed: 0,
      iterations: 0,
      maxIterations: 10,
      toolsUsed: [],
      repairAttempts: 0,
      filesChanged: 0,
      model: '',
    },
  }
}

// --- Public API -----------------------------------------------------------

/**
 * Start an agent task on the backend.
 *
 * `onEvent` receives a start event immediately, then the run's activity
 * events in sequence. `onComplete` fires once the run result is known.
 */
export async function startAgentTask(
  task: string,
  workspaceId: string = 'local-project',
  onEvent: (event: ActivityEvent) => void,
  onComplete: (run: AgentRunView) => void,
  model?: string,
): Promise<void> {
  onEvent({ id: 'ev-0', time: clock(), text: `Task accepted: ${task}`, state: 'ANALYZING', status: 'done' })

  try {
    const response = await fetch(`${API_BASE}/agent/analyze`, {
      method: 'POST',
      headers: await authedHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ workspace_id: workspaceId, task, ...(model ? { model } : {}) }),
    })

    if (!response.ok) {
      let detail = `API error ${response.status}`
      try {
        const err = await response.json()
        if (err?.detail) detail = String(err.detail)
      } catch { /* keep default */ }
      if (isAuthFailure(response.status)) {
        detail = `${detail} (sign in again, or configure Supabase auth)`
      }
      throw new Error(detail)
    }

    const data: AnalysisResponse = await response.json()
    const run = mapAnalysis(data)
    const rest = run.events
    rest.forEach((event, i) => {
      setTimeout(() => onEvent({ ...event, time: clock() }), (i + 1) * 110)
    })
    setTimeout(() => onComplete(run), (rest.length + 1) * 110 + 60)
  } catch (error) {
    let message = error instanceof Error ? error.message : 'Backend request failed'
    if (message === 'Failed to fetch' || message.toLowerCase().includes('networkerror')) {
      message = `Backend unreachable at ${API_BASE.replace(/\/api\/v1$/, '')} — check that the backend server is running.`
    }
    const run = failureRun(task, message)
    setTimeout(() => onEvent(run.events[1]), 120)
    setTimeout(() => onComplete(run), 260)
  }
}

/** List configured workspaces (real git metadata from the backend). */
export async function fetchWorkspaces(): Promise<WorkspaceInfo[]> {
  const res = await fetch(`${API_BASE}/workspaces`, { headers: await authedHeaders() })
  if (!res.ok) throw new Error(await readError(res, 'Workspaces request failed'))
  return res.json()
}

/**
 * Shallow-clone a GitHub repository on the backend and register it as a
 * workspace. Returns the new workspace info (id, name, path, branch).
 */
export async function cloneGitHubRepo(owner: string, name: string): Promise<WorkspaceInfo> {
  const res = await fetch(`${API_BASE}/repos/clone`, {
    method: 'POST',
    headers: await authedHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ owner, name }),
  })
  if (!res.ok) throw new Error(await readError(res, 'Repository clone failed'))
  return res.json()
}

/** Commit the latest run's selected files on a new branch and push to GitHub. */
export async function publishWorkspaceChanges(
  workspaceId: string,
  files: string[],
  branchName: string,
  commitMessage: string,
  githubToken: string,
): Promise<PublishChangesResult> {
  const response = await fetch(
    `${API_BASE}/workspaces/${encodeURIComponent(workspaceId)}/git/publish`,
    {
      method: 'POST',
      headers: await authedHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        files,
        branch_name: branchName,
        commit_message: commitMessage,
        github_token: githubToken,
      }),
    },
  )
  const body = await response.json().catch(() => ({})) as Record<string, unknown>
  if (!response.ok) {
    throw new Error(typeof body.detail === 'string' ? body.detail : `GitHub update failed (${response.status})`)
  }
  return body as unknown as PublishChangesResult
}

/** Load the actual working-tree diff when the agent omitted diff output. */
export async function fetchWorkspaceDiff(
  workspaceId: string,
  files: string[],
): Promise<{ diff: string; truncated: boolean }> {
  const params = new URLSearchParams()
  files.forEach(path => params.append('files', path))
  const response = await fetch(
    `${API_BASE}/workspaces/${encodeURIComponent(workspaceId)}/git/diff?${params}`,
    { headers: await authedHeaders() },
  )
  if (!response.ok) throw new Error(await readError(response, 'Could not load workspace diff'))
  return response.json()
}

/** Fetch the file tree of a workspace. */
export async function fetchTree(workspaceId: string): Promise<RepoNode> {
  const res = await fetch(`${API_BASE}/workspaces/${encodeURIComponent(workspaceId)}/tree`, {
    headers: await authedHeaders(),
  })
  if (!res.ok) throw new Error(await readError(res, 'Tree request failed'))
  return res.json()
}

/** Read a single file from the workspace. */
export async function fetchFile(workspaceId: string, path: string): Promise<FilePayload> {
  const res = await fetch(
    `${API_BASE}/workspaces/${encodeURIComponent(workspaceId)}/file?path=${encodeURIComponent(path)}`,
    { headers: await authedHeaders() },
  )
  if (!res.ok) throw new Error(await readError(res, 'File request failed'))
  return res.json()
}

/** Extract a useful error message from a failed response. */
async function readError(res: Response, fallback: string): Promise<string> {
  let detail = `${fallback} (${res.status})`
  try {
    const err = await res.json()
    if (err?.detail) detail = String(err.detail)
  } catch { /* keep default */ }
  if (isAuthFailure(res.status)) {
    detail = `${detail} (sign in again, or configure Supabase auth)`
  }
  return detail
}

/** Check whether the backend is reachable. */
export async function checkHealth(): Promise<{ status: string; message: string }> {
  try {
    const res = await fetch(HEALTH_URL)
    if (!res.ok) throw new Error(`Health check failed (${res.status})`)
    return await res.json()
  } catch {
    return { status: 'unhealthy', message: 'Backend not reachable' }
  }
}
