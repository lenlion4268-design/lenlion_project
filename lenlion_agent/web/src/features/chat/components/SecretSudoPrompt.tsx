import { useState } from 'react'
import { useStore } from '@nanostores/react'
import { chatState, respondSecret } from '@/features/chat/chatStore'
import styles from './Dialog.module.css'

export function SecretSudoPrompt() {
  const { secret } = useStore(chatState)
  const [value, setValue] = useState('')
  if (!secret) return null

  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <h3>{secret.kind === 'sudo' ? 'Sudo' : 'Secret'}</h3>
        <p>{secret.prompt}</p>
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={secret.envVar || 'Enter value'}
        />
        <div className={styles.actions}>
          <button
            type="button"
            className="btn"
            onClick={() => {
              void respondSecret(value)
              setValue('')
            }}
          >
            Submit
          </button>
        </div>
      </div>
    </div>
  )
}
