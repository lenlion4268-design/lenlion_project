import { useEffect } from 'react'
import { initChat, resetChatStore } from '@/features/chat/chatStore'
import { StatusBanner } from '@/features/chat/components/StatusBanner'
import { Reasoning } from '@/features/chat/components/Reasoning'
import { ToolActivity } from '@/features/chat/components/ToolActivity'
import { MessageList } from '@/features/chat/components/MessageList'
import { Composer } from '@/features/chat/components/Composer'
import { ApprovalDialog } from '@/features/chat/components/ApprovalDialog'
import { ClarifyDialog } from '@/features/chat/components/ClarifyDialog'
import { SecretSudoPrompt } from '@/features/chat/components/SecretSudoPrompt'
import styles from './ChatPage.module.css'

export function ChatPage() {
  useEffect(() => {
    void initChat()
    return () => resetChatStore()
  }, [])

  return (
    <div className={styles.chat}>
      <StatusBanner />
      <Reasoning />
      <ToolActivity />
      <MessageList />
      <Composer />
      <ApprovalDialog />
      <ClarifyDialog />
      <SecretSudoPrompt />
    </div>
  )
}
