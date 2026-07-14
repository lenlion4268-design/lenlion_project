import { useStore } from '@nanostores/react'
import { chatState } from '@/features/chat/chatStore'
import styles from './StatusBanner.module.css'

export function StatusBanner() {
  const { connected, connecting, error, statusText } = useStore(chatState)

  if (error) {
    return <div className={`${styles.banner} ${styles.error}`}>{error}</div>
  }
  if (connecting) {
    return <div className={styles.banner}>Connecting…</div>
  }
  if (!connected) {
    return <div className={styles.banner}>Disconnected</div>
  }
  if (statusText) {
    return <div className={styles.banner}>{statusText}</div>
  }
  return null
}
