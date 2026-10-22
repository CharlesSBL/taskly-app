import type { InputHTMLAttributes, TextareaHTMLAttributes } from 'react'

type BaseProps = {
  /** Optional label shown above the field. */
  label?: string
  /** Legacy helper alias for backward compatibility. */
  hint?: string
  /** Helper text shown below the field. */
  helperText?: string
  /** Error message shown below the field. */
  error?: string
  /** Optional tooltip text displayed from the label icon. */
  tooltip?: string
  /** Field interaction state. */
  state?: 'normal' | 'disabled' | 'locked'
  /** Render a multiline textarea instead of an input. */
  multiline?: boolean
  /** Number of rows for multiline mode. */
  rows?: number
}

/** Props for the Input component. */
export type InputProps = BaseProps &
  InputHTMLAttributes<HTMLInputElement> &
  TextareaHTMLAttributes<HTMLTextAreaElement>
