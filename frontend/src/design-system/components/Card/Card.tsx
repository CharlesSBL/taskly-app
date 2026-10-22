import { BaseCard } from './Card.styles'
import type { CardProps } from './Card.types'

/**
 * Surface container used to group related content and actions.
 */
export function Card({ variant = 'outline', ...props }: CardProps) {
  return <BaseCard {...props} $variant={variant} />
}
