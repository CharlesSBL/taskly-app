import { BaseButton } from './Button.styles'
import type { ButtonProps, ButtonState } from './Button.types'

/**
 * Design-system button with semantic variant, size, and interaction state.
 */
export function Button({
  variant = 'primary',
  size = 'medium',
  state,
  fullWidth,
  lockedIcon = '🔒',
  children,
  disabled,
  ...props
}: ButtonProps) {
  const resolvedState: ButtonState = state ?? (disabled ? 'disabled' : 'normal')
  const isDisabled =
    disabled || resolvedState === 'disabled' || resolvedState === 'locked'
  const content =
    resolvedState === 'locked' ? (
      <>
        <span aria-hidden="true">{lockedIcon}</span>
        <span>{children ?? 'Locked'}</span>
      </>
    ) : (
      children
    )

  return (
    <BaseButton
      {...props}
      disabled={isDisabled}
      $variant={variant}
      $size={size}
      $state={resolvedState}
      $fullWidth={fullWidth}
    >
      {content}
    </BaseButton>
  )
}
