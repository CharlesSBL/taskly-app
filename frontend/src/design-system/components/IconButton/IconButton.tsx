import { BaseIconButton } from './IconButton.styles'
import type { IconButtonProps, IconButtonState } from './IconButton.types'

/**
 * Compact button for icon-only actions with variant, size, and state controls.
 */
export function IconButton({
  variant = 'solid',
  size = 'medium',
  state,
  lockedIcon = '🔒',
  children,
  disabled,
  ...props
}: IconButtonProps) {
  const resolvedState: IconButtonState =
    state ?? (disabled ? 'disabled' : 'normal')
  const isDisabled =
    disabled || resolvedState === 'disabled' || resolvedState === 'locked'
  const content = resolvedState === 'locked' ? lockedIcon : children

  return (
    <BaseIconButton
      {...props}
      disabled={isDisabled}
      $variant={variant}
      $size={size}
      $state={resolvedState}
    >
      {content}
    </BaseIconButton>
  )
}
