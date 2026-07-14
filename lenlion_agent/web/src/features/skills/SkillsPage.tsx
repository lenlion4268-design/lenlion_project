import { useEffect, useState } from 'react'
import { apiGet, apiPut } from '@/lib/apiClient'
import { PageHeader } from '@/components/layout/PageHeader'
import { Panel } from '@/components/layout/Panel'

interface Skill {
  name: string
  category?: string
  description?: string
  enabled?: boolean
}

export function SkillsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [skills, setSkills] = useState<Skill[]>([])

  async function load() {
    setLoading(true)
    setError('')
    try {
      const res = await apiGet<{ skills?: Skill[] } | Skill[]>('/skills')
      setSkills(Array.isArray(res) ? res : res.skills ?? [])
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
    await apiPut('/skills/toggle', { name, enabled })
    await load()
  }

  return (
    <div className="page">
      <PageHeader title="技能" subtitle="启用或禁用 Agent 技能" />
      <Panel loading={loading} error={error}>
        <div className="list">
          {skills.map((skill) => (
            <div key={skill.name} className="listItem">
              <div>
                <strong>{skill.name}</strong>
                {skill.category ? <span className="badge">{skill.category}</span> : null}
                {skill.description ? (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {skill.description}
                  </div>
                ) : null}
              </div>
              <input
                type="checkbox"
                checked={!!skill.enabled}
                onChange={(e) => void toggle(skill.name, e.target.checked)}
              />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
