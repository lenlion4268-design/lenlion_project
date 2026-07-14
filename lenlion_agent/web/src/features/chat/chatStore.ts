import { atom } from 'nanostores'
import MarkdownIt from 'markdown-it'
import {
  fetchWsTicket,
  GatewayClient,
  type GatewayEventHandler,
} from '@/lib/gatewayClient'
import {
  createInitialChatState,
  nextMsgId,
  reduceChatEvent,
  type ChatUiState,
} from '@/features/chat/chatEventReducer'

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

export const chatState = atom<ChatUiState>(createInitialChatState())
let client: GatewayClient | null = null

function patchChat(patch: Partial<ChatUiState>): void {
  chatState.set({ ...chatState.get(), ...patch })
}

function applyEvent(ev: Parameters<GatewayEventHandler>[0]): void {
  chatState.set(reduceChatEvent(chatState.get(), ev, nextMsgId))
}

export function renderMarkdown(text: string): string {
  return md.render(text || '')
}

export async function initChat(): Promise<void> {
  const state = chatState.get()
  if (state.connecting || state.connected) return
  patchChat({ connecting: true, error: '' })
  try {
    if (window.__HERMES_AUTH_REQUIRED__) {
      await fetchWsTicket()
    }
    const gw = new GatewayClient()
    gw.onEvent(applyEvent)
    await gw.connect()
    client = gw
    const session = await gw.createSession()
    patchChat({ connected: true, sessionId: session.session_id })
  } catch (e) {
    patchChat({
      error: e instanceof Error ? e.message : String(e),
    })
  } finally {
    patchChat({ connecting: false })
  }
}

export async function submitPrompt(text: string): Promise<void> {
  const state = chatState.get()
  if (!client || !state.sessionId || !text.trim()) return
  chatState.set({
    ...state,
    messages: [...state.messages, { id: nextMsgId(), role: 'user', text: text.trim() }],
    tools: [],
    error: '',
    running: true,
  })
  await client.request('prompt.submit', {
    session_id: state.sessionId,
    text: text.trim(),
  })
}

export async function interruptChat(): Promise<void> {
  const state = chatState.get()
  if (!client || !state.sessionId) return
  await client.request('session.interrupt', { session_id: state.sessionId })
  patchChat({ running: false })
}

export async function respondClarify(answer: string): Promise<void> {
  const state = chatState.get()
  if (!client || !state.sessionId || !state.clarify) return
  await client.request('clarify.respond', {
    session_id: state.sessionId,
    request_id: state.clarify.requestId,
    answer,
  })
  patchChat({ clarify: null })
}

export async function respondApproval(choice: 'approve' | 'deny'): Promise<void> {
  const state = chatState.get()
  if (!client || !state.sessionId || !state.approval) return
  await client.request('approval.respond', {
    session_id: state.sessionId,
    request_id: state.approval.requestId,
    choice,
  })
  patchChat({ approval: null })
}

export async function respondSecret(value: string): Promise<void> {
  const state = chatState.get()
  if (!client || !state.sessionId || !state.secret) return
  const method = state.secret.kind === 'sudo' ? 'sudo.respond' : 'secret.respond'
  await client.request(method, {
    session_id: state.sessionId,
    request_id: state.secret.requestId,
    answer: value,
  })
  patchChat({ secret: null })
}

export function resetChatStore(): void {
  client?.close()
  client = null
  chatState.set(createInitialChatState())
}
