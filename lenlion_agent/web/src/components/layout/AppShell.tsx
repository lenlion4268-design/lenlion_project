import { Outlet, useLocation } from 'react-router-dom'
import { AppSidebar } from '@/components/layout/AppSidebar'
import { ErrorBoundary } from '@/components/layout/ErrorBoundary'
import { navTitle, type NavId } from '@/app/nav'
import styles from './AppShell.module.css'

const PATH_TO_NAV: Record<string, NavId> = {
  '/overview': 'overview',
  '/chat': 'chat',
  '/model': 'model',
  '/config': 'config',
  '/keys': 'keys',
  '/tools': 'tools',
  '/skills': 'skills',
  '/mcp': 'mcp',
  '/gateway': 'gateway',
  '/cron': 'cron',
  '/sessions': 'sessions',
  '/logs': 'logs',
}

export function AppShell() {
  const location = useLocation()
  const navId = PATH_TO_NAV[location.pathname] ?? 'overview'
  const isChat = navId === 'chat'

  return (
    <div className={styles.platform}>
      <AppSidebar />
      <main className={`${styles.main} ${isChat ? styles.chat : ''}`}>
        {!isChat ? <div className={styles.mobileTitle}>{navTitle(navId)}</div> : null}
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  )
}
