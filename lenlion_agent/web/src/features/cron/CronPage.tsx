import { useEffect, useState } from 'react'
import { apiGet } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface CronJob {
  id?: string
  name?: string
  schedule?: string
  status?: string
}

export function CronPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [jobs, setJobs] = useState<CronJob[]>([])

  useEffect(() => {
    void (async () => {
      setLoading(true)
      setError('')
      try {
        const res = await apiGet<{ jobs?: CronJob[] } | CronJob[]>('/cron/jobs')
        setJobs(Array.isArray(res) ? res : res.jobs ?? [])
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  return (
    <div className="page">
      <PageHeader title="定时任务" subtitle="Cron 任务列表（只读）" />
      <Panel loading={loading} error={error}>
        {jobs.length === 0 ? (
          <p className="hint">暂无定时任务。使用 CLI 或 Agent cronjob 工具创建。</p>
        ) : (
          <div className="list">
            {jobs.map((job, i) => (
              <div key={job.id || job.name || i} className="listItem">
                <div>
                  <strong>{job.name || job.id || '—'}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {job.schedule || '—'}
                  </div>
                </div>
                <span className="badge">{job.status || 'unknown'}</span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
