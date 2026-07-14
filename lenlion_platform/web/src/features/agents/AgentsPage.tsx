import { useEffect, useState } from 'react'
import { useStore } from '@nanostores/react'
import { adminGet, adminPost } from '@/lib/adminApiClient'
import type { AdminAgentRow, Paginated } from '@/lib/types'
import { tenantId } from '@/features/auth/authStore'

export function AgentsPage() {
  const tid = useStore(tenantId)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [agents, setAgents] = useState<AdminAgentRow[]>([])
  const [confirmId, setConfirmId] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await adminGet<Paginated<AdminAgentRow>>('/admin/agents', {
        tenant_id: tid,
        limit: '50',
      })
      setAgents(res.items)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [tid])

  async function revoke(agentId: string) {
    try {
      await adminPost(`/admin/agents/${encodeURIComponent(agentId)}/revoke`)
      setConfirmId(null)
      await load()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="page">
      <h1>Agents</h1>
      <p className="hint">Tenant: {tid}</p>
      {loading ? <p className="hint">加载中…</p> : null}
      {error ? <p className="error">{error}</p> : null}
      {!loading && !error && agents.length === 0 ? (
        <p className="hint">暂无 Agent</p>
      ) : null}
      <div className="list">
        {agents.map((agent) => (
          <div key={agent.id} className="listItem">
            <div>
              <strong>{agent.name}</strong>
              <div className="hint">{agent.id}</div>
              <div className="hint">
                {agent.hostname} · {agent.version} · {agent.status}
              </div>
            </div>
            <div>
              {agent.revoked_at ? (
                <span className="badge revoked">已撤销</span>
              ) : confirmId === agent.id ? (
                <>
                  <button type="button" className="btn danger" onClick={() => void revoke(agent.id)}>
                    确认撤销
                  </button>
                  <button type="button" className="btn" onClick={() => setConfirmId(null)}>
                    取消
                  </button>
                </>
              ) : (
                <button type="button" className="btn danger" onClick={() => setConfirmId(agent.id)}>
                  撤销
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
