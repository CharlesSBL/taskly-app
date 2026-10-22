import type { HTMLAttributes } from 'react'

export type AlertVariant = 'info' | 'success' | 'warning'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant
}
