import { useState, type KeyboardEvent } from 'react'
import { useStore } from '@nanostores/react'
import { chatState, interruptChat, submitPrompt } from '@/features/chat/chatStore'
import styles from './Composer.module.css'

export function Composer() {
  const { connected, connecting, running } = useStore(chatState)
  const [input, setInput] = useState('')

  async function send() {
    const text = input
    setInput('')
    await submitPrompt(text)
  }

  function onKeyDown(ev: KeyboardEvent<HTMLTextAreaElement>) {
    if (ev.key === 'Enter' && !ev.shiftKey) {
      ev.preventDefault()
      void send()
    }
  }

  return (
    <div className={styles.composer}>
      <textarea
        rows={3}
        value={input}
        placeholder="Message Lenlion… (Enter to send, Shift+Enter for newline)"
        disabled={!connected || connecting}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={onKeyDown}
      />
      <div className={styles.actions}>
        <button type="button" className={styles.stop} disabled={!running} onClick={() => void interruptChat()}>
          Stop
        </button>
        <button
          type="button"
          className={styles.send}
          disabled={!connected || !input.trim()}
          onClick={() => void send()}
        >
          Send
        </button>
      </div>
    </div>
  )
}
