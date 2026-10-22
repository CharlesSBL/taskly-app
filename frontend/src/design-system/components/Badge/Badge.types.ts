import type { HTMLAttributes } from 'react'

export type BadgeVariant = 'neutral' | 'info' | 'success' | 'warning'

/** Props for the Badge component. */
export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  /** Visual style of the badge. */
  variant?: BadgeVariant
}
