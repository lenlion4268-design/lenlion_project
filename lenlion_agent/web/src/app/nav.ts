export type NavId =
  | 'overview'
  | 'chat'
  | 'model'
  | 'config'
  | 'keys'
  | 'tools'
  | 'skills'
  | 'mcp'
  | 'gateway'
  | 'cron'
  | 'sessions'
  | 'logs'

export interface NavItem {
  id: NavId
  label: string
  icon: string
  group: 'main' | 'manage' | 'system'
  path: string
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'overview', label: '概览', icon: '◉', group: 'main', path: '/overview' },
  { id: 'chat', label: '聊天', icon: '💬', group: 'main', path: '/chat' },
  { id: 'model', label: '模型', icon: '🧠', group: 'manage', path: '/model' },
  { id: 'config', label: '配置', icon: '⚙', group: 'manage', path: '/config' },
  { id: 'keys', label: '密钥', icon: '🔑', group: 'manage', path: '/keys' },
  { id: 'tools', label: '工具集', icon: '🛠', group: 'manage', path: '/tools' },
  { id: 'skills', label: '技能', icon: '📚', group: 'manage', path: '/skills' },
  { id: 'mcp', label: 'MCP', icon: '🔌', group: 'manage', path: '/mcp' },
  { id: 'gateway', label: '消息网关', icon: '📡', group: 'system', path: '/gateway' },
  { id: 'cron', label: '定时任务', icon: '⏰', group: 'system', path: '/cron' },
  { id: 'sessions', label: '会话', icon: '🗂', group: 'system', path: '/sessions' },
  { id: 'logs', label: '日志', icon: '📋', group: 'system', path: '/logs' },
]

export const NAV_GROUPS = [
  { key: 'main' as const, label: '工作台' },
  { key: 'manage' as const, label: '配置' },
  { key: 'system' as const, label: '系统' },
]

export function navTitle(id: NavId): string {
  return NAV_ITEMS.find((item) => item.id === id)?.label ?? 'Lenlion'
}
