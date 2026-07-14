export interface AdminAgentRow {
  id: string
  tenant_id: string
  name: string
  hostname: string
  version: string
  status: string
  last_heartbeat?: number | null
  revoked_at?: number | null
  created_at: number
}

export interface AdminAuditEventRow {
  id: string
  tenant_id: string
  agent_id?: string | null
  session_id?: string | null
  kind: string
  payload: Record<string, unknown>
  created_at: number
}

export interface AdminApprovalRow {
  id: string
  tenant_id: string
  agent_id: string
  session_id: string
  tool: string
  decision: string
  decided_by: string
  reason: string
  created_at: number
  consumed_at?: number | null
}

export interface Paginated<T> {
  items: T[]
  next_cursor?: string | null
}
