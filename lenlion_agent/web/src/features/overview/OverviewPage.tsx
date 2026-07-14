import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'
import styles from './OverviewPage.module.css'

interface Status {
  version?: string
  gateway_running?: boolean
  gateway_state?: string
  active_sessions?: number
  hermes_home?: string
}

export function OverviewPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [status, setStatus] = useState<Status | null>(null)
  const [doctorOutput, setDoctorOutput] = useState('')
  const [doctorLoading, setDoctorLoading] = useState(false)

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        setStatus(await apiGet<Status>('/status'))
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  async function runDoctor() {
    setDoctorLoading(true)
    setDoctorOutput('')
    try {
      const res = await apiPost<{ output?: string; report?: string }>('/ops/doctor')
      setDoctorOutput(res.output || res.report || JSON.stringify(res, null, 2))
    } catch (e) {
      setDoctorOutput(e instanceof Error ? e.message : String(e))
    } finally {
      setDoctorLoading(false)
    }
  }

  return (
    <div className="page">
      <PageHeader title="概览" subtitle="运行状态与健康检查" />
      <div className={styles.grid}>
        <Panel loading={loading} error={error}>
          {status ? (
            <div className={styles.stats}>
              <div className={styles.stat}>
                <span className={styles.label}>版本</span>
                <span className={styles.value}>{status.version || '—'}</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.label}>网关</span>
                <span
                  className={`${styles.value} ${status.gateway_running ? styles.ok : styles.warn}`}
                >
                  {status.gateway_running ? '运行中' : '未运行'}
                  {status.gateway_state ? `（${status.gateway_state}）` : ''}
                </span>
              </div>
              <div className={styles.stat}>
                <span className={styles.label}>活跃会话</span>
                <span className={styles.value}>{status.active_sessions ?? 0}</span>
              </div>
              {status.hermes_home ? (
                <div className={`${styles.stat} ${styles.wide}`}>
                  <span className={styles.label}>数据目录</span>
                  <span className={`${styles.value} ${styles.mono}`}>{status.hermes_home}</span>
                </div>
              ) : null}
            </div>
          ) : null}
        </Panel>
        <Panel title="环境诊断">
          <p className="hint">
            运行 <code>lenlion doctor</code> 检查配置与依赖。
          </p>
          <button type="button" className="btn" disabled={doctorLoading} onClick={() => void runDoctor()}>
            {doctorLoading ? '检查中…' : '运行诊断'}
          </button>
          {doctorOutput ? <pre className="output">{doctorOutput}</pre> : null}
        </Panel>
      </div>
    </div>
  )
}
