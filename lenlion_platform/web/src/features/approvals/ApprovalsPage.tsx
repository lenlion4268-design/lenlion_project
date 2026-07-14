import { useEffect, useState } from 'react'
import { useStore } from '@nanostores/react'
import { adminGet } from '@/lib/adminApiClient'
import type { AdminApprovalRow, Paginated } from '@/lib/types'
import { tenantId } from '@/features/auth/authStore'

export function ApprovalsPage() {
  const tid = useStore(tenantId)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [rows, setRows] = useState<AdminApprovalRow[]>([])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const res = await adminGet<Paginated<AdminApprovalRow>>('/admin/approvals', {
          tenant_id: tid,
          limit: '50',
        })
        setRows(res.items)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [tid])

  return (
    <div className="page">
      <h1>Approvals</h1>
      {loading ? <p className="hint">加载中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error && rows.length === 0 ? <p className="hint">暂无审批记录</p> : null}
      <div className="list">
        {rows.map((row) => (
          <div key={row.id} className="listItem">
            <div>
              <strong>{row.tool}</strong>
              <div className="hint">
                {row.decision} · {row.decided_by} · {row.reason}
              </div>
              <div className="hint">agent={row.agent_id}</div>
            </div>
            <span className="badge">{new Date(row.created_at * 1000).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
