import { useEffect, useState } from 'react'
import { apiGet, apiPut } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

export function ConfigPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [language, setLanguage] = useState('en')
  const [configJson, setConfigJson] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const config = await apiGet<Record<string, unknown>>('/config')
        setConfigJson(JSON.stringify(config, null, 2))
        const display = config.display as { language?: string } | undefined
        setLanguage(display?.language || 'en')
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  async function save() {
    setSaving(true)
    setMessage('')
    try {
      const config = JSON.parse(configJson) as Record<string, unknown>
      const display = (config.display as Record<string, unknown> | undefined) ?? {}
      display.language = language
      config.display = display
      await apiPut('/config', config)
      setConfigJson(JSON.stringify(config, null, 2))
      setMessage('已保存')
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <PageHeader title="配置" subtitle="界面语言与完整 config.yaml" />
      <Panel loading={loading} error={error}>
        <div className="formGrid">
          <label>
            界面语言
            <select value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="en">English</option>
              <option value="zh">中文</option>
            </select>
          </label>
          <button type="button" className="btn" disabled={saving} onClick={() => void save()}>
            保存
          </button>
        </div>
        {message ? <p className="message">{message}</p> : null}
        <details style={{ marginTop: '1rem' }}>
          <summary>完整配置 JSON</summary>
          <pre className="output">{configJson}</pre>
        </details>
      </Panel>
    </div>
  )
}
