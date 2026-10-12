export type AgentState =
  | 'READY' | 'ANALYZING' | 'EXPLORING' | 'SEARCHING' | 'READING'
  | 'PLANNING' | 'IMPLEMENTING' | 'MODIFICATION' | 'TESTING' | 'FAILURE_ANALYSIS'
  | 'REPAIR' | 'VERIFICATION' | 'COMPLETED' | 'FAILED'

export type ViewId =
  | 'repositories' | 'files' | 'agent' | 'changes' | 'tests'
  | 'architecture' | 'prompt' | 'usage' | 'efficiency'

export type RunTab = 'activity' | 'changes' | 'tests' | 'verification'

export type EventStatus = 'done' | 'active' | 'failed'

export interface ActivityEvent {
  id: string
  time: string
  text: string
  state: AgentState
  status: EventStatus
  detail?: string
}

export interface RepoNode {
  name: string
  path: string
  type: 'dir' | 'file'
  children?: RepoNode[]
}

export interface WorkspaceInfo {
  id: string
  name: string
  path: string
  branch: string
}

export interface RepoSummary {
  owner: string
  name: string
  language: string
  stars: number
  updated: string
  visibility?: 'public' | 'private'
  fork?: boolean
}

export type DiffKind = 'context' | 'add' | 'del'

export interface DiffLine {
  kind: DiffKind
  oldNo?: number
  newNo?: number
  text: string
}

export interface FileChange {
  path: string
  added: number
  removed: number
  lines: DiffLine[]
}

export interface TestCase {
  name: string
  passed: boolean
  seconds: number
}

export interface TestRun {
  tests: TestCase[]
  durationSeconds: number
}

/** Real per-run metrics reported by the backend. */
export interface RunMetrics {
  durationSeconds: number
  tokensUsed: number
  iterations: number
  maxIterations: number
  toolsUsed: string[]
  repairAttempts: number
  filesChanged: number
  model: string
}

/** One agent run as mapped from the backend analysis response. */
export interface AgentRunView {
  success: boolean
  status: string
  message: string
  events: ActivityEvent[]
  plan: string[]
  filesInspected: string[]
  filesChanged: string[]
  changes: FileChange[]
  tests: TestRun | null
  metrics: RunMetrics
}
