import type { HTMLAttributes } from 'react'

export type CardVariant = 'outline' | 'elevated'

/** Props for the Card component. */
export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  /** Visual style of the card. */
  variant?: CardVariant
}
