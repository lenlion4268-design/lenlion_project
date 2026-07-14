import { useStore } from '@nanostores/react'
import { chatState, respondApproval } from '@/features/chat/chatStore'
import styles from './Dialog.module.css'

export function ApprovalDialog() {
  const { approval } = useStore(chatState)
  if (!approval) return null

  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        <h3>Approval required</h3>
        <pre className={styles.command}>{approval.command}</pre>
        {approval.description ? <p>{approval.description}</p> : null}
        <div className={styles.actions}>
          <button type="button" className="btn" onClick={() => void respondApproval('approve')}>
            Approve
          </button>
          <button type="button" className="btn" onClick={() => void respondApproval('deny')}>
            Deny
          </button>
        </div>
      </div>
    </div>
  )
}
