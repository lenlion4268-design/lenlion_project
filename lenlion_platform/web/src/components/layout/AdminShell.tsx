import { NavLink, Outlet } from 'react-router-dom'
import { clearAdminSession } from '@/features/auth/authStore'
import styles from './AdminShell.module.css'

export function AdminShell() {
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `${styles.navItem} ${isActive ? styles.active : ''}`

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <strong>Lenlion</strong>
          <span>Platform Admin</span>
        </div>
        <nav>
          <NavLink to="/agents" className={navClass}>
            Agents
          </NavLink>
          <NavLink to="/audit" className={navClass}>
            Audit Events
          </NavLink>
          <NavLink to="/approvals" className={navClass}>
            Approvals
          </NavLink>
        </nav>
        <button type="button" className="btn" onClick={() => clearAdminSession()}>
          退出
        </button>
      </aside>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
