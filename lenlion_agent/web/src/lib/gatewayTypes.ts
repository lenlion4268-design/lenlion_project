export interface HermesBootstrap {
  __HERMES_SESSION_TOKEN__?: string
  __HERMES_BASE_PATH__?: string
  __HERMES_AUTH_REQUIRED__?: boolean
}

export type GatewayEventType =
  | 'gateway.ready'
  | 'gateway.stderr'
  | 'gateway.protocol_error'
  | 'session.info'
  | 'message.start'
  | 'message.delta'
  | 'message.complete'
  | 'thinking.delta'
  | 'reasoning.delta'
  | 'status.update'
  | 'tool.generating'
  | 'tool.start'
  | 'tool.complete'
  | 'clarify.request'
  | 'approval.request'
  | 'sudo.request'
  | 'secret.request'
  | 'notification.show'
  | 'notification.clear'
  | 'error'

export interface GatewayEventEnvelope {
  type: GatewayEventType
  session_id?: string
  payload?: Record<string, unknown>
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  text: string
  streaming?: boolean
}

export interface ToolCallState {
  toolId: string
  name: string
  argsText?: string
  resultText?: string
  error?: string
  durationS?: number
  status: 'generating' | 'running' | 'done' | 'error'
}

export interface ClarifyPrompt {
  requestId: string
  question: string
  choices: string[]
}

export interface ApprovalPrompt {
  requestId: string
  command: string
  description?: string
}

export interface SecretPrompt {
  requestId: string
  prompt: string
  envVar?: string
  kind: 'sudo' | 'secret'
}

export interface SessionCreateResult {
  session_id: string
  stored_session_id?: string
}

declare global {
  interface Window extends HermesBootstrap {}
}

export {}
