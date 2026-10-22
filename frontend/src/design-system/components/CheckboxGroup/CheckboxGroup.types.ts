/** Props for the CheckboxGroup component. */
export interface CheckboxGroupProps {
  /** Group label displayed above the options. */
  label: string
  /** Optional tooltip text displayed from the label icon. */
  tooltip?: string
  /** Available checkbox options. */
  options: string[]
  /** Currently selected values. */
  value: string[]
  /** Called when the selection changes. */
  onChange: (next: string[]) => void
  /** Optional helper text. */
  helper?: string
  /** Optional error message. */
  error?: string
  /** Disable all checkboxes. */
  disabled?: boolean
}
