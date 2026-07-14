import { useStore } from '@nanostores/react'
import { type ReactNode, useState } from 'react'
import { adminToken, setAdminToken, setTenantId, tenantId } from '@/features/auth/authStore'

export function LoginGate({ children }: { children: ReactNode }) {
  const token = useStore(adminToken)
  const currentTenant = useStore(tenantId)
  const [draftToken, setDraftToken] = useState('')
  const [draftTenant, setDraftTenant] = useState(currentTenant)

  if (token) return children

  return (
    <div className="login panel">
      <h1>Lenlion Platform Admin</h1>
      <p className="hint">Admin token 仅保存在内存中，刷新页面后需重新输入。</p>
      <label>
        Admin Token
        <input
          type="password"
          value={draftToken}
          onChange={(e) => setDraftToken(e.target.value)}
          placeholder="Bearer token value"
        />
      </label>
      <label>
        Tenant ID
        <input
          value={draftTenant}
          onChange={(e) => setDraftTenant(e.target.value)}
          placeholder="tenant_dev"
        />
      </label>
      <button
        type="button"
        className="btn"
        disabled={!draftToken.trim() || !draftTenant.trim()}
        onClick={() => {
          setAdminToken(draftToken.trim())
          setTenantId(draftTenant.trim())
        }}
      >
        进入管理台
      </button>
    </div>
  )
}
