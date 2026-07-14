import type { GatewayEventEnvelope, SessionCreateResult } from './gatewayTypes'

type Pending = {
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
}

export type GatewayEventHandler = (event: GatewayEventEnvelope) => void

let nextId = 1

export function buildWsUrl(): string {
  const base = window.__HERMES_BASE_PATH__ || ''
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const params = new URLSearchParams()
  if (window.__HERMES_AUTH_REQUIRED__) {
    const ticket = sessionStorage.getItem('hermes_ws_ticket')
    if (ticket) params.set('ticket', ticket)
  } else if (window.__HERMES_SESSION_TOKEN__) {
    params.set('token', window.__HERMES_SESSION_TOKEN__)
  }
  const qs = params.toString()
  return `${proto}//${window.location.host}${base}/api/ws${qs ? `?${qs}` : ''}`
}

export class GatewayClient {
  private ws: WebSocket | null = null
  private pending = new Map<string, Pending>()
  private eventHandlers = new Set<GatewayEventHandler>()
  private readyPromise: Promise<void> | null = null
  private readyResolve: (() => void) | null = null

  connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) return Promise.resolve()
    this.readyPromise = new Promise((resolve) => {
      this.readyResolve = resolve
    })
    this.ws = new WebSocket(buildWsUrl())
    this.ws.onmessage = (ev) => this.onMessage(String(ev.data))
    this.ws.onclose = () => {
      this.rejectAll(new Error('WebSocket closed'))
    }
    this.ws.onerror = () => {
      this.rejectAll(new Error('WebSocket error'))
    }
    return new Promise((resolve, reject) => {
      if (!this.ws) return reject(new Error('WebSocket not created'))
      this.ws.onopen = () => resolve()
      this.ws.onerror = () => reject(new Error('WebSocket failed to open'))
    })
  }

  onEvent(handler: GatewayEventHandler): () => void {
    this.eventHandlers.add(handler)
    return () => this.eventHandlers.delete(handler)
  }

  async waitReady(): Promise<void> {
    if (this.readyPromise) await this.readyPromise
  }

  async request<T = unknown>(method: string, params: Record<string, unknown> = {}): Promise<T> {
    const ws = this.ws
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      throw new Error('Gateway not connected')
    }
    const id = `r${nextId++}`
    const payload = { jsonrpc: '2.0', id, method, params }
    const result = new Promise<T>((resolve, reject) => {
      this.pending.set(id, { resolve: resolve as (v: unknown) => void, reject })
    })
    ws.send(JSON.stringify(payload))
    return result
  }

  async createSession(): Promise<SessionCreateResult> {
    await this.waitReady()
    return this.request<SessionCreateResult>('session.create', {})
  }

  handleRawMessage(raw: string): void {
    this.onMessage(raw)
  }

  private onMessage(raw: string): void {
    let msg: Record<string, unknown>
    try {
      msg = JSON.parse(raw) as Record<string, unknown>
    } catch {
      this.emit({ type: 'gateway.protocol_error', payload: { message: raw } })
      return
    }

    if (msg.method === 'event') {
      const params = (msg.params || {}) as Record<string, unknown>
      const envelope: GatewayEventEnvelope = {
        type: params.type as GatewayEventEnvelope['type'],
        session_id: params.session_id as string | undefined,
        payload: (params.payload as Record<string, unknown>) || undefined,
      }
      if (envelope.type === 'gateway.ready') {
        this.readyResolve?.()
        this.readyResolve = null
      }
      this.emit(envelope)
      return
    }

    const id = msg.id as string | undefined
    if (!id) return
    const pending = this.pending.get(id)
    if (!pending) return
    this.pending.delete(id)
    if (msg.error) {
      const err = msg.error as { message?: string }
      pending.reject(new Error(err.message || 'RPC error'))
    } else {
      pending.resolve(msg.result)
    }
  }

  private emit(event: GatewayEventEnvelope): void {
    for (const h of this.eventHandlers) h(event)
  }

  private rejectAll(err: Error): void {
    for (const [, p] of this.pending) p.reject(err)
    this.pending.clear()
  }

  close(): void {
    this.ws?.close()
    this.ws = null
  }
}

export async function fetchWsTicket(): Promise<string | null> {
  if (!window.__HERMES_AUTH_REQUIRED__) return null
  const base = window.__HERMES_BASE_PATH__ || ''
  const res = await fetch(`${base}/api/auth/ws-ticket`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!res.ok) return null
  const data = (await res.json()) as { ticket?: string }
  if (data.ticket) sessionStorage.setItem('hermes_ws_ticket', data.ticket)
  return data.ticket || null
}
