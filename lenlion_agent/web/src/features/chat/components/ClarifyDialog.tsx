import { useStore } from '@nanostores/react'
import { chatState, respondClarify } from '@/features/chat/chatStore'
import styles from './Dialog.module.css'

export function ClarifyDialog() {
  const { clarify } = useStore(chatState)
  if (!clarify) return null

  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <h3>Clarify</h3>
        <p>{clarify.question}</p>
        <div className={styles.actions}>
          {clarify.choices.map((choice) => (
            <button key={choice} type="button" className="btn" onClick={() => void respondClarify(choice)}>
              {choice}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
