import type { ButtonHTMLAttributes, ReactNode } from 'react'

export type IconButtonSize = 'small' | 'medium' | 'large'
export type IconButtonState = 'normal' | 'disabled' | 'locked'

/** Props for the IconButton component. */
export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual emphasis of the icon button. */
  variant?: 'solid' | 'ghost'
  /** Size of the icon button. */
  size?: IconButtonSize
  /** Interaction state of the icon button. */
  state?: IconButtonState
  /** Optional icon content used when state is locked. */
  lockedIcon?: ReactNode
}
