import { useEffect, useState } from 'react'
import { useStore } from '@nanostores/react'
import { adminGet } from '@/lib/adminApiClient'
import type { AdminAuditEventRow, Paginated } from '@/lib/types'
import { tenantId } from '@/features/auth/authStore'

export function AuditPage() {
  const tid = useStore(tenantId)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [events, setEvents] = useState<AdminAuditEventRow[]>([])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const res = await adminGet<Paginated<AdminAuditEventRow>>('/admin/audit-events', {
          tenant_id: tid,
          limit: '50',
        })
        setEvents(res.items)
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [tid])

  return (
    <div className="page">
      <h1>Audit Events</h1>
      {loading ? <p className="hint">加载中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error && events.length === 0 ? (
        <p className="hint">暂无审计事件</p>
      ) : null}
      <div className="list">
        {events.map((ev) => (
          <div key={ev.id} className="listItem">
            <div>
              <strong>{ev.kind}</strong>
              <div className="hint">
                agent={ev.agent_id || '—'} · session={ev.session_id || '—'}
              </div>
              <pre className="hint">{JSON.stringify(ev.payload, null, 2)}</pre>
            </div>
            <span className="badge">{new Date(ev.created_at * 1000).toLocaleString()}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
