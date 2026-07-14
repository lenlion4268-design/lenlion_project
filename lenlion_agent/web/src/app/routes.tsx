import { createHashRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { OverviewPage } from '@/features/overview/OverviewPage'
import { ChatPage } from '@/features/chat/ChatPage'
import { ModelPage } from '@/features/model/ModelPage'
import { ConfigPage } from '@/features/config/ConfigPage'
import { EnvPage } from '@/features/env/EnvPage'
import { ToolsPage } from '@/features/tools/ToolsPage'
import { SkillsPage } from '@/features/skills/SkillsPage'
import { McpPage } from '@/features/mcp/McpPage'
import { GatewayPage } from '@/features/gateway/GatewayPage'
import { CronPage } from '@/features/cron/CronPage'
import { SessionsPage } from '@/features/sessions/SessionsPage'
import { LogsPage } from '@/features/logs/LogsPage'

export const router = createHashRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/overview" replace /> },
      { path: 'overview', element: <OverviewPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'model', element: <ModelPage /> },
      { path: 'config', element: <ConfigPage /> },
      { path: 'keys', element: <EnvPage /> },
      { path: 'tools', element: <ToolsPage /> },
      { path: 'skills', element: <SkillsPage /> },
      { path: 'mcp', element: <McpPage /> },
      { path: 'gateway', element: <GatewayPage /> },
      { path: 'cron', element: <CronPage /> },
      { path: 'sessions', element: <SessionsPage /> },
      { path: 'logs', element: <LogsPage /> },
    ],
  },
])
