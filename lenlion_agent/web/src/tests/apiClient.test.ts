import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { buildAuthHeaders, getApiBase } from '@/lib/apiClient'

describe('apiClient', () => {
  beforeEach(() => {
    window.__HERMES_BASE_PATH__ = '/prefix'
    window.__HERMES_SESSION_TOKEN__ = 'tok-abc'
  })

  afterEach(() => {
    delete window.__HERMES_BASE_PATH__
    delete window.__HERMES_SESSION_TOKEN__
  })

  it('builds api base with prefix', () => {
    expect(getApiBase()).toBe('/prefix/api')
  })

  it('includes session token header', () => {
    expect(buildAuthHeaders()['X-Hermes-Session-Token']).toBe('tok-abc')
  })
})

describe('apiGet', () => {
  beforeEach(() => {
    window.__HERMES_BASE_PATH__ = ''
    window.__HERMES_SESSION_TOKEN__ = 'tok'
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('throws parsed error on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        statusText: 'Bad Request',
        text: async () => JSON.stringify({ detail: 'nope' }),
      }),
    )
    const { apiGet } = await import('@/lib/apiClient')
    await expect(apiGet('/status')).rejects.toThrow('nope')
  })
})
