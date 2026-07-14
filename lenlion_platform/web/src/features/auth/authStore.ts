import { atom } from 'nanostores'

export const adminToken = atom<string>('')
export const tenantId = atom<string>('tenant_dev')

export function setAdminToken(token: string): void {
  adminToken.set(token)
}

export function clearAdminSession(): void {
  adminToken.set('')
}

export function setTenantId(id: string): void {
  tenantId.set(id)
}
