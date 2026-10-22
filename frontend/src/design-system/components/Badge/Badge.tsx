import { BaseBadge } from './Badge.styles'
import type { BadgeProps } from './Badge.types'

/**
 * Compact status label used to display lightweight semantic state.
 */
export function Badge({ variant = 'neutral', ...props }: BadgeProps) {
  return <BaseBadge {...props} $variant={variant} />
}
