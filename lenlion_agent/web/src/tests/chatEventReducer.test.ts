import { describe, expect, it } from 'vitest'
import {
  createInitialChatState,
  reduceChatEvent,
} from '@/features/chat/chatEventReducer'

describe('reduceChatEvent', () => {
  it('ignores events for a different session', () => {
    const state = { ...createInitialChatState(), sessionId: 's1' }
    const next = reduceChatEvent(state, {
      type: 'message.delta',
      session_id: 's2',
      payload: { text: 'hi' },
    })
    expect(next).toBe(state)
  })

  it('handles message streaming lifecycle', () => {
    let id = 0
    const nextId = () => `m${++id}`
    let state = createInitialChatState()
    state = { ...state, sessionId: 's1' }

    state = reduceChatEvent(state, { type: 'message.start', session_id: 's1' }, nextId)
    expect(state.running).toBe(true)
    expect(state.messages).toHaveLength(1)
    expect(state.messages[0]?.streaming).toBe(true)

    state = reduceChatEvent(
      state,
      { type: 'message.delta', session_id: 's1', payload: { text: 'Hel' } },
      nextId,
    )
    expect(state.messages[0]?.text).toBe('Hel')

    state = reduceChatEvent(
      state,
      { type: 'message.complete', session_id: 's1', payload: { text: 'Hello' } },
      nextId,
    )
    expect(state.messages[0]?.text).toBe('Hello')
    expect(state.messages[0]?.streaming).toBe(false)
    expect(state.running).toBe(false)
  })

  it('handles approval request', () => {
    const state = reduceChatEvent(
      { ...createInitialChatState(), sessionId: 's1' },
      {
        type: 'approval.request',
        session_id: 's1',
        payload: { request_id: 'r1', command: 'rm -rf /' },
      },
    )
    expect(state.approval?.command).toBe('rm -rf /')
  })

  it('handles error event', () => {
    const state = reduceChatEvent(
      createInitialChatState(),
      { type: 'error', payload: { message: 'boom' } },
    )
    expect(state.error).toBe('boom')
    expect(state.running).toBe(false)
  })
})
