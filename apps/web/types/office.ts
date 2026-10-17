// Shared contract for the Office view. Built by composables/useOffice.ts from real API responses;
// components must render only what is passed in (no invented data).

export type Priority = 'must' | 'should' | 'could' | 'wont'
export type ChangeKind = 'added' | 'modified' | 'removed' | null

export interface Citation { paragraph_id: string; quote: string; status: string }

export interface Card {
  id: string                      // requirement id, e.g. "REQ-3"
  title: string
  priority: Priority
  beforePriority?: Priority | null // set when change === 'modified' and priority moved
  change: ChangeKind               // null = unchanged / first analysis
  proposed: boolean                // true until a PM approves (render dashed / "proposed")
  est?: { low?: number; high?: number; pert?: number } | null // person-hours from triage
  staff: { staff_id: string; name: string; reason?: string }[] // recommended, needs human approval
  citations?: Citation[]
  story?: { as_a?: string; i_want?: string; so_that?: string } | null
  acceptance_criteria?: string[]
  reason?: string                  // why it changed (v2 diff)
}

export interface Leave { type: string; from: string; to: string }

export interface Staff {
  id: string                       // "S01"
  name: string
  role: string
  projects: string[]
  weekly_capacity_h?: number
  allocated_h?: number
  on_leave: Leave | null           // from GET /api/staff
}

// Where the office helper (the AI agent) is and what it is doing.
export type Phase =
  | 'idle'          // waiting at the helper desk
  | 'receiving'     // walking to the drop chute to pick up a document
  | 'reading'       // at the triage desk, local Nemotron is running
  | 'quarantine'    // reporting an ignored embedded instruction
  | 'filing'        // walking to the kanban wall, proposed cards appear
  | 'awaiting'      // proposed board waiting on PM approval
  | 'applied'       // PM approved; staff walk to their work
  | 'error'         // a real call failed; show the error, never fake a result
