import type { SelectHTMLAttributes } from 'react'

export interface SelectOption {
  /** Value submitted in forms. */
  value: string
  /** Visible label for the option. */
  label: string
}

/** Props for the Select component. */
export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
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
  /** Options to render. */
  options: SelectOption[]
}
