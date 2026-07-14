import { useEffect, useState } from 'react'
import { apiGet } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface McpServer {
  name: string
  transport?: string
  command?: string
  enabled?: boolean
}

export function McpPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [servers, setServers] = useState<McpServer[]>([])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiGet<{ servers?: McpServer[] } | McpServer[]>('/mcp/servers')
        setServers(Array.isArray(res) ? res : res.servers ?? [])
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="page">
      <PageHeader title="MCP" subtitle="Model Context Protocol 服务器" />
      <Panel loading={loading} error={error}>
        {servers.length === 0 ? (
          <p className="hint">暂无 MCP 服务器。使用 CLI：<code>lenlion mcp</code></p>
        ) : (
          <div className="list">
            {servers.map((s) => (
              <div key={s.name} className="listItem">
                <div>
                  <strong>{s.name}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {s.transport || s.command || '—'}
                  </div>
                </div>
                <span className={`badge ${s.enabled ? 'ok' : ''}`}>
                  {s.enabled ? '已启用' : '未启用'}
                </span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
