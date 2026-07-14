import { createHashRouter, Navigate } from 'react-router-dom'
import { AdminShell } from '@/components/layout/AdminShell'
import { LoginGate } from '@/features/auth/LoginGate'
import { AgentsPage } from '@/features/agents/AgentsPage'
import { AuditPage } from '@/features/audit/AuditPage'
import { ApprovalsPage } from '@/features/approvals/ApprovalsPage'

export const router = createHashRouter([
  {
    path: '/',
    element: (
      <LoginGate>
        <AdminShell />
      </LoginGate>
    ),
    children: [
      { index: true, element: <Navigate to="/agents" replace /> },
      { path: 'agents', element: <AgentsPage /> },
      { path: 'audit', element: <AuditPage /> },
      { path: 'approvals', element: <ApprovalsPage /> },
    ],
  },
])
