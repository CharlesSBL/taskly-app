import type { InputHTMLAttributes } from 'react'

/** Props for the Checkbox component. */
export interface CheckboxProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'type'
> {
  /** Label shown next to the checkbox. */
  label: string
}
