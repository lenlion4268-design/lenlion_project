import { useEffect, useState } from 'react'
import { apiGet, apiPut } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface Toolset {
  name: string
  label?: string
  description?: string
  enabled?: boolean
  configured?: boolean
  tool_count?: number
}

export function ToolsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toolsets, setToolsets] = useState<Toolset[]>([])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await apiGet<{ toolsets?: Toolset[] } | Toolset[]>('/tools/toolsets')
      setToolsets(Array.isArray(res) ? res : res.toolsets ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function toggle(name: string, enabled: boolean) {
    await apiPut(`/tools/toolsets/${encodeURIComponent(name)}`, { enabled })
    await load()
  }

  return (
    <div className="page">
      <PageHeader title="工具集" subtitle="启用或禁用 Agent 工具集" />
      <Panel loading={loading} error={error}>
        <div className="list">
          {toolsets.map((ts) => (
            <div key={ts.name} className="listItem">
              <div>
                <strong>{ts.label || ts.name}</strong>
                {ts.description ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{ts.description}</div>
                ) : null}
                {ts.configured === false ? (
                  <div style={{ fontSize: '0.75rem', color: 'var(--warning)' }}>未配置依赖</div>
                ) : null}
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="checkbox"
                  checked={!!ts.enabled}
                  onChange={(e) => void toggle(ts.name, e.target.checked)}
                />
                {ts.tool_count != null ? `${ts.tool_count} 工具` : ''}
              </label>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
