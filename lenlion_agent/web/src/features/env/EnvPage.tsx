import { useEffect, useState } from 'react'
import { apiGet, apiPut } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface EnvEntry {
  key: string
  value?: string
  description?: string
  channel_managed?: boolean
}

export function EnvPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [entries, setEntries] = useState<EnvEntry[]>([])
  const [editingKey, setEditingKey] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [message, setMessage] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await apiGet<{ vars?: EnvEntry[] } | EnvEntry[]>('/env?lang=zh')
      const list = Array.isArray(res) ? res : res.vars ?? []
      setEntries(list.filter((e) => !e.channel_managed))
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function save(key: string) {
    setMessage('')
    try {
      await apiPut('/env', { key, value: editValue })
      setEditingKey(null)
      setEditValue('')
      await load()
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="page">
      <PageHeader title="密钥" subtitle="API Key 与环境变量" />
      <Panel loading={loading} error={error}>
        <div className="list">
          {entries.map((entry) => (
            <div key={entry.key} className="listItem">
              <div>
                <strong>{entry.key}</strong>
                {entry.description ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {entry.description}
                  </div>
                ) : null}
                {editingKey === entry.key ? (
                  <input
                    type="password"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    style={{ marginTop: '0.5rem', width: '100%' }}
                  />
                ) : (
                  <div style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
                    {entry.value || '（未设置）'}
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                {editingKey === entry.key ? (
                  <>
                    <button type="button" className="btn" onClick={() => void save(entry.key)}>
                      保存
                    </button>
                    <button type="button" className="btn" onClick={() => setEditingKey(null)}>
                      取消
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    className="btn"
                    onClick={() => {
                      setEditingKey(entry.key)
                      setEditValue('')
                    }}
                  >
                    编辑
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
        {message ? <p className="message">{message}</p> : null}
      </Panel>
    </div>
  )
}
