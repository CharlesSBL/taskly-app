import { useId } from 'react'
import type { CheckboxProps } from './Checkbox.types'
import { Box, HiddenInput, Label, Wrapper } from './Checkbox.styles'

/**
 * Checkbox control with a custom visual box and associated text label.
 */
export function Checkbox({ label, id, ...props }: CheckboxProps) {
  const generatedId = useId()
  const checkboxId = id ?? generatedId

  return (
    <Wrapper htmlFor={checkboxId}>
      <HiddenInput id={checkboxId} type="checkbox" {...props} />
      <Box aria-hidden="true" />
      <Label>{label}</Label>
    </Wrapper>
  )
}
