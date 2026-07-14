import { useEffect, useMemo, useState } from 'react'
import { apiGet, apiPost } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface ModelInfo {
  model?: string
  provider?: string
  effective_context_length?: number
}

interface ProviderRow {
  id: string
  name: string
  authenticated?: boolean
  models?: Array<{ id: string; name?: string }>
}

interface ModelOptions {
  providers?: ProviderRow[]
  current?: { provider?: string; model?: string }
}

export function ModelPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [info, setInfo] = useState<ModelInfo | null>(null)
  const [options, setOptions] = useState<ModelOptions | null>(null)
  const [selectedProvider, setSelectedProvider] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const providers = options?.providers ?? []

  async function load() {
    setLoading(true)
    setError('')
    setMessage('')
    try {
      const [modelInfo, modelOptions] = await Promise.all([
        apiGet<ModelInfo>('/model/info'),
        apiGet<ModelOptions>('/model/options'),
      ])
      setInfo(modelInfo)
      setOptions(modelOptions)
      setSelectedProvider(
        modelOptions.current?.provider || modelInfo.provider || modelOptions.providers?.[0]?.id || '',
      )
      setSelectedModel(modelOptions.current?.model || modelInfo.model || '')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const modelsForProvider = useMemo(() => {
    return providers.find((p) => p.id === selectedProvider)?.models ?? []
  }, [providers, selectedProvider])

  async function save() {
    if (!selectedProvider || !selectedModel) return
    setSaving(true)
    setMessage('')
    try {
      const res = await apiPost<{ ok?: boolean; confirm_required?: boolean; confirm_message?: string }>(
        '/model/set',
        { scope: 'main', provider: selectedProvider, model: selectedModel },
      )
      if (res.confirm_required) {
        setMessage(res.confirm_message || '需要确认昂贵模型')
      } else {
        setMessage('已保存（对新会话生效）')
        await load()
      }
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <PageHeader title="模型" subtitle="选择推理提供方与默认模型" />
      <Panel loading={loading} error={error}>
        {info ? (
          <div style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
            当前：<strong>{info.provider || '—'}</strong> / <strong>{info.model || '—'}</strong>
            {info.effective_context_length ? (
              <span style={{ color: 'var(--text-dim)' }}>
                {' '}
                · 上下文 {Math.round(info.effective_context_length / 1000)}K
              </span>
            ) : null}
          </div>
        ) : null}
        <div className="formGrid">
          <label>
            提供方
            <select value={selectedProvider} onChange={(e) => setSelectedProvider(e.target.value)}>
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                  {p.authenticated === false ? '（未配置）' : ''}
                </option>
              ))}
            </select>
          </label>
          <label>
            模型
            <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
              <option value="">— 选择模型 —</option>
              {modelsForProvider.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name || m.id}
                </option>
              ))}
            </select>
          </label>
          <button type="button" className="btn" disabled={saving} onClick={() => void save()}>
            保存
          </button>
        </div>
        {message ? <p className="message">{message}</p> : null}
      </Panel>
    </div>
  )
}
