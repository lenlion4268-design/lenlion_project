import { useEffect, useState } from 'react'
import { apiGet } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface SessionRow {
  id?: string
  title?: string
  updated_at?: string
  message_count?: number
  active?: boolean
}

export function SessionsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [sessions, setSessions] = useState<SessionRow[]>([])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiGet<{ sessions?: SessionRow[] } | SessionRow[]>(
          '/sessions?limit=50&order=recent',
        )
        setSessions(Array.isArray(res) ? res : res.sessions ?? [])
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="page">
      <PageHeader title="会话" subtitle="最近 50 个会话" />
      <Panel loading={loading} error={error}>
        <div className="list">
          {sessions.map((s) => (
            <div key={s.id} className="listItem">
              <div>
                <strong>{s.title || s.id || '—'}</strong>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {s.updated_at || '—'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {s.active ? <span className="badge ok">活跃</span> : null}
                <span className="badge">{s.message_count ?? 0} 消息</span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
