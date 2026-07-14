import { atom } from 'nanostores'

export const sidebarCollapsed = atom(false)

export function toggleSidebar(): void {
  sidebarCollapsed.set(!sidebarCollapsed.get())
}
