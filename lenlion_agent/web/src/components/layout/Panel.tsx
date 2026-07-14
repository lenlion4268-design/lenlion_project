import type { ReactNode } from 'react'
import styles from './Panel.module.css'

type PanelProps = {
  title?: string
  loading?: boolean
  error?: string
  children?: ReactNode
}

export function Panel({ title, loading, error, children }: PanelProps) {
  return (
    <section className={styles.panel}>
      {title ? <h3>{title}</h3> : null}
      {loading ? <div className={styles.state}>加载中…</div> : null}
      {!loading && error ? <div className={`${styles.state} ${styles.error}`}>{error}</div> : null}
      {!loading && !error ? children : null}
    </section>
  )
}
