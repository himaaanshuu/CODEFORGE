export type AgentState =
  | 'READY' | 'ANALYZING' | 'EXPLORING' | 'SEARCHING' | 'READING'
  | 'PLANNING' | 'IMPLEMENTING' | 'MODIFICATION' | 'TESTING' | 'FAILURE_ANALYSIS'
  | 'REPAIR' | 'VERIFICATION' | 'COMPLETED' | 'FAILED'

export type ViewId = 'repository' | 'files' | 'agent' | 'changes' | 'tests'

export type EventStatus = 'done' | 'active' | 'failed'

export interface ActivityEvent {
  id: string
  time: string
  text: string
  state: AgentState
  status: EventStatus
}

export interface RepoNode {
  name: string
  path: string
  type: 'dir' | 'file'
  children?: RepoNode[]
}

export interface Repository {
  name: string
  owner: string
  branch: string
  language: string
  files: number
  description: string
  tree: RepoNode[]
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

export interface TestSuite {
  name: string
  passed: number
  failed: number
}

export interface TestRun {
  suites: TestSuite[]
  durationSeconds: number
}

export interface TaskResult {
  summary: string
  filesChanged: number
  testsPassed: number
  regressions: number
}

/** Shape the real backend client should return. Replace data/mockAgent.ts with an API-backed implementation. */
export interface AgentRun {
  events: ActivityEvent[]
  changes: FileChange[]
  tests: TestRun
  result: TaskResult
  repairAttempts: number
  verification: VerificationResult
}

export interface VerificationResult {
  targetIssueResolved: boolean
  regressionSuitePassed: boolean
  changesValidated: boolean
}
