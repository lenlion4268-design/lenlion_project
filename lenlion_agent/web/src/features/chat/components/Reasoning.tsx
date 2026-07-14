import { useStore } from '@nanostores/react'
import { chatState } from '@/features/chat/chatStore'
import styles from './Reasoning.module.css'

export function Reasoning() {
  const { reasoning } = useStore(chatState)
  if (!reasoning) return null
  return (
    <details className={styles.reasoning}>
      <summary>Reasoning</summary>
      <pre>{reasoning}</pre>
    </details>
  )
}
