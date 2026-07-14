import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface Platform {
  name: string
  configured?: boolean
  connected?: boolean
  status?: string
}

export function GatewayPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await apiGet<{ platforms?: Platform[] } | Platform[]>('/messaging/platforms')
      setPlatforms(Array.isArray(res) ? res : res.platforms ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  async function start() {
    setBusy(true)
    setMessage('')
    try {
      await apiPost('/gateway/start')
      setMessage('网关已启动')
      await load()
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function stop() {
    setBusy(true)
    setMessage('')
    try {
      await apiPost('/gateway/stop')
      setMessage('网关已停止')
      await load()
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <PageHeader
        title="消息网关"
        subtitle="Telegram、Discord 等平台消息接入"
        actions={
          <>
            <button type="button" className="btn" disabled={busy} onClick={() => void start()}>
              启动
            </button>
            <button type="button" className="btn" disabled={busy} onClick={() => void stop()}>
              停止
            </button>
          </>
        }
      />
      <Panel loading={loading} error={error}>
        {message ? <p className="message">{message}</p> : null}
        <div className="list">
          {platforms.map((p) => (
            <div key={p.name} className="listItem">
              <strong>{p.name}</strong>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <span className={`badge ${p.configured ? 'ok' : 'warn'}`}>
                  {p.configured ? '已配置' : '未配置'}
                </span>
                <span className={`badge ${p.connected ? 'ok' : ''}`}>
                  {p.connected ? '已连接' : p.status || '未连接'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
