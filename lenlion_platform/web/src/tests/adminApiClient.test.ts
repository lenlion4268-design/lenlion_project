import { describe, expect, it } from 'vitest'
import { buildAuthHeaders, getApiBase } from '@/lib/adminApiClient'
import { adminToken } from '@/features/auth/authStore'

describe('adminApiClient', () => {
  it('builds bearer header from memory token', () => {
    adminToken.set('secret-token')
    expect(buildAuthHeaders().Authorization).toBe('Bearer secret-token')
    adminToken.set('')
  })

  it('uses same-origin api base', () => {
    expect(getApiBase()).toBe('')
  })
})
