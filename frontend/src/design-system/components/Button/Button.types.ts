import type { ButtonHTMLAttributes, ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
export type ButtonSize = 'small' | 'medium' | 'large'
export type ButtonState = 'normal' | 'disabled' | 'locked'

/** Props for the Button component. */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style of the button. */
  variant?: ButtonVariant
  /** Size of the button. */
  size?: ButtonSize
  /** Interaction state of the button. */
  state?: ButtonState
  /** Optional full-width layout. */
  fullWidth?: boolean
  /** Optional lock icon content shown when state is locked. */
  lockedIcon?: ReactNode
}
