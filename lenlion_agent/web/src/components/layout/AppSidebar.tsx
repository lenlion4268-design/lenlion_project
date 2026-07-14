import { NavLink } from 'react-router-dom'
import { useStore } from '@nanostores/react'
import { NAV_GROUPS, NAV_ITEMS } from '@/app/nav'
import { sidebarCollapsed, toggleSidebar } from '@/app/shellStore'
import styles from './AppSidebar.module.css'

export function AppSidebar() {
  const collapsed = useStore(sidebarCollapsed)

  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      <div className={styles.brand}>
        <span className={styles.logo}>L</span>
        {!collapsed ? (
          <div className={styles.brandText}>
            <strong>Lenlion</strong>
            <span>Agent Platform</span>
          </div>
        ) : null}
      </div>

      <nav className={styles.nav}>
        {NAV_GROUPS.map((group) => (
          <div key={group.key}>
            {!collapsed ? <div className={styles.groupLabel}>{group.label}</div> : null}
            {NAV_ITEMS.filter((item) => item.group === group.key).map((item) => (
              <NavLink
                key={item.id}
                to={item.path}
                title={item.label}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <span className={styles.icon}>{item.icon}</span>
                {!collapsed ? <span className={styles.label}>{item.label}</span> : null}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <button
        type="button"
        className={styles.collapseBtn}
        title={collapsed ? '展开侧栏' : '收起侧栏'}
        onClick={() => toggleSidebar()}
      >
        {collapsed ? '»' : '«'}
      </button>
    </aside>
  )
}
