import { useStore } from '@nanostores/react'
import { chatState, renderMarkdown } from '@/features/chat/chatStore'
import styles from './MessageList.module.css'

export function MessageList() {
  const { messages, connected } = useStore(chatState)

  return (
    <div className={styles.messages}>
      {messages.map((msg) => (
        <div key={msg.id} className={`${styles.message} ${styles[msg.role]}`}>
          <div className={styles.role}>{msg.role === 'user' ? 'You' : 'Assistant'}</div>
          <div
            className={`${styles.body} markdown`}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
          />
          {msg.streaming ? <span className={styles.cursor}>▍</span> : null}
        </div>
      ))}
      {!messages.length && connected ? (
        <p className={styles.empty}>Send a message to start chatting.</p>
      ) : null}
    </div>
  )
}
