import type {
  ApprovalPrompt,
  ChatMessage,
  ClarifyPrompt,
  GatewayEventEnvelope,
  SecretPrompt,
  ToolCallState,
} from '@/lib/gatewayTypes'

export interface ChatUiState {
  connected: boolean
  connecting: boolean
  sessionId: string
  messages: ChatMessage[]
  tools: ToolCallState[]
  reasoning: string
  statusText: string
  running: boolean
  error: string
  clarify: ClarifyPrompt | null
  approval: ApprovalPrompt | null
  secret: SecretPrompt | null
}

export function createInitialChatState(): ChatUiState {
  return {
    connected: false,
    connecting: false,
    sessionId: '',
    messages: [],
    tools: [],
    reasoning: '',
    statusText: '',
    running: false,
    error: '',
    clarify: null,
    approval: null,
    secret: null,
  }
}

let msgCounter = 0

export function nextMsgId(): string {
  return `m${++msgCounter}`
}

export function resetMsgCounter(): void {
  msgCounter = 0
}

export function reduceChatEvent(
  state: ChatUiState,
  ev: GatewayEventEnvelope,
  nextId: () => string = nextMsgId,
): ChatUiState {
  if (ev.session_id && state.sessionId && ev.session_id !== state.sessionId) {
    return state
  }
  const p = ev.payload || {}

  switch (ev.type) {
    case 'message.start':
      return {
        ...state,
        running: true,
        reasoning: '',
        messages: [
          ...state.messages,
          { id: nextId(), role: 'assistant', text: '', streaming: true },
        ],
      }
    case 'message.delta': {
      const text = String(p.text || '')
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last?.role === 'assistant' && last.streaming) {
        messages[messages.length - 1] = { ...last, text: last.text + text }
      }
      return { ...state, messages }
    }
    case 'message.complete': {
      const text = String(p.text || '')
      const messages = [...state.messages]
      const last = messages[messages.length - 1]
      if (last?.role === 'assistant') {
        messages[messages.length - 1] = {
          ...last,
          text: text || last.text,
          streaming: false,
        }
      }
      return { ...state, messages, running: false, statusText: '' }
    }
    case 'thinking.delta':
    case 'reasoning.delta':
      return { ...state, reasoning: state.reasoning + String(p.text || '') }
    case 'tool.generating':
      return {
        ...state,
        tools: [
          ...state.tools,
          {
            toolId: String(p.name || 'tool'),
            name: String(p.name || 'tool'),
            status: 'generating',
          },
        ],
      }
    case 'tool.start': {
      const toolId = String(p.tool_id || p.name || nextId())
      const tools = [...state.tools]
      const existing = tools.find((t) => t.toolId === toolId)
      const entry: ToolCallState = {
        toolId,
        name: String(p.name || 'tool'),
        argsText: p.args_text ? String(p.args_text) : undefined,
        status: 'running',
      }
      if (existing) {
        Object.assign(existing, entry)
      } else {
        tools.push(entry)
      }
      return { ...state, tools }
    }
    case 'tool.complete': {
      const toolId = String(p.tool_id || p.name || '')
      const tools = state.tools.map((t) => {
        if (t.toolId !== toolId && t.name !== p.name) return t
        return {
          ...t,
          status: (p.error ? 'error' : 'done') as ToolCallState['status'],
          resultText: p.result_text ? String(p.result_text) : undefined,
          error: p.error ? String(p.error) : undefined,
          durationS: typeof p.duration_s === 'number' ? p.duration_s : undefined,
        }
      })
      return { ...state, tools }
    }
    case 'status.update':
      return { ...state, statusText: String(p.text || p.kind || '') }
    case 'clarify.request':
      return {
        ...state,
        clarify: {
          requestId: String(p.request_id || ''),
          question: String(p.question || ''),
          choices: Array.isArray(p.choices) ? p.choices.map(String) : [],
        },
      }
    case 'approval.request':
      return {
        ...state,
        approval: {
          requestId: String(p.request_id || ''),
          command: String(p.command || ''),
          description: p.description ? String(p.description) : undefined,
        },
      }
    case 'sudo.request':
      return {
        ...state,
        secret: {
          requestId: String(p.request_id || ''),
          prompt: 'Sudo password required',
          kind: 'sudo',
        },
      }
    case 'secret.request':
      return {
        ...state,
        secret: {
          requestId: String(p.request_id || ''),
          prompt: String(p.prompt || 'Secret required'),
          envVar: p.env_var ? String(p.env_var) : undefined,
          kind: 'secret',
        },
      }
    case 'notification.show':
      return { ...state, statusText: String(p.text || '') }
    case 'notification.clear':
      return { ...state, statusText: '' }
    case 'error':
      return {
        ...state,
        error: String(p.message || 'Unknown error'),
        running: false,
      }
    default:
      return state
  }
}
