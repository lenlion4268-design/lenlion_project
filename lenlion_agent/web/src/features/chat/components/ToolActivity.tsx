import { useStore } from '@nanostores/react'
import { chatState } from '@/features/chat/chatStore'
import styles from './ToolActivity.module.css'

export function ToolActivity() {
  const { tools } = useStore(chatState)
  if (!tools.length) return null

  return (
    <div className={styles.tools}>
      {tools.map((t) => (
        <div key={t.toolId} className={styles.tool}>
          <span className={styles.name}>{t.name}</span>
          <span className={`${styles.status} ${styles[t.status]}`}>{t.status}</span>
          {t.argsText ? <pre className={styles.args}>{t.argsText}</pre> : null}
          {t.resultText ? <pre className={styles.result}>{t.resultText}</pre> : null}
          {t.error ? <pre className={styles.error}>{t.error}</pre> : null}
        </div>
      ))}
    </div>
  )
}
