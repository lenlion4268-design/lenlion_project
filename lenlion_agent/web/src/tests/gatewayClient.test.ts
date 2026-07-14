import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { GatewayClient, buildWsUrl } from '@/lib/gatewayClient'

class MockWebSocket {
  static OPEN = 1
  readyState = MockWebSocket.OPEN
  onopen: (() => void) | null = null
  onmessage: ((ev: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  send = vi.fn()
  close = vi.fn()

  constructor(_url: string) {
    queueMicrotask(() => this.onopen?.())
  }
}

describe('GatewayClient', () => {
  beforeEach(() => {
    vi.stubGlobal('WebSocket', MockWebSocket as unknown as typeof WebSocket)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('resolves RPC responses by id', async () => {
    const client = new GatewayClient()
    await client.connect()
    const promise = client.request<{ ok: boolean }>('session.create', {})
    client.handleRawMessage(
      JSON.stringify({ jsonrpc: '2.0', id: 'r1', result: { ok: true } }),
    )
    await expect(promise).resolves.toEqual({ ok: true })
  })

  it('emits gateway events', () => {
    const client = new GatewayClient()
    const events: string[] = []
    client.onEvent((ev) => events.push(ev.type))
    client.handleRawMessage(
      JSON.stringify({
        jsonrpc: '2.0',
        method: 'event',
        params: { type: 'message.delta', payload: { text: 'x' } },
      }),
    )
    expect(events).toEqual(['message.delta'])
  })

  it('builds ws url with token', () => {
    window.__HERMES_SESSION_TOKEN__ = 'abc123'
    window.__HERMES_AUTH_REQUIRED__ = false
    expect(buildWsUrl()).toContain('token=abc123')
    delete window.__HERMES_SESSION_TOKEN__
  })
})
