import type { ReactNode } from 'react'

/** Props for the Drawer component. */
export interface DrawerProps {
  /** Drawer title shown in the header. */
  title: string
  /** Controls visibility. */
  isOpen: boolean
  /** Called when the drawer should close. */
  onClose: () => void
  /** Drawer content. */
  children: ReactNode
  /** Prevent closing while a request is in progress. */
  busy?: boolean
}
