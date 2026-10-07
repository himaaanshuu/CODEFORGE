import type { AgentState } from '../types'

export interface StateMeta { label: string; dot: string; active: boolean }

/** Colors reference Tailwind token classes only. */
export const stateMeta: Record<AgentState, StateMeta> = {
  READY: { label: 'READY', dot: 'bg-sage', active: false },
  ANALYZING: { label: 'ANALYZING', dot: 'bg-denim', active: true },
  EXPLORING: { label: 'EXPLORING', dot: 'bg-denim', active: true },
  SEARCHING: { label: 'SEARCHING', dot: 'bg-denim', active: true },
  READING: { label: 'READING', dot: 'bg-denim', active: true },
  PLANNING: { label: 'PLANNING', dot: 'bg-burgundy-light', active: true },
  IMPLEMENTING: { label: 'IMPLEMENTING', dot: 'bg-burgundy-light', active: true },
  MODIFICATION: { label: 'MODIFICATION', dot: 'bg-burgundy', active: true },
  TESTING: { label: 'TESTING', dot: 'bg-sage-light', active: true },
  FAILURE_ANALYSIS: { label: 'FAILURE_ANALYSIS', dot: 'bg-blue-gray', active: true },
  REPAIR: { label: 'REPAIR', dot: 'bg-burgundy', active: true },
  VERIFICATION: { label: 'VERIFICATION', dot: 'bg-sage-light', active: true },
  COMPLETED: { label: 'COMPLETED', dot: 'bg-sage', active: false },
  FAILED: { label: 'FAILED', dot: 'bg-rust', active: false },
}
