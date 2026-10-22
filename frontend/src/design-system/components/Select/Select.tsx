import { useId } from 'react'
import type { SelectProps } from './Select.types'
import {
  Control,
  ControlShell,
  Field,
  Helper,
  Label,
  LabelRow,
  LockIcon,
  TooltipIcon,
} from './Select.styles'

/**
 * Select field with label, helper/error text, tooltip, and locked state support.
 */
export function Select({
  label,
  hint,
  helperText,
  error,
  tooltip,
  state = 'normal',
  options,
  id,
  disabled,
  ...props
}: SelectProps) {
  const generatedId = useId()
  const selectId = id ?? generatedId
  const resolvedState = disabled ? 'disabled' : state
  const isLocked = resolvedState === 'locked'
  const isDisabled = resolvedState === 'disabled' || isLocked
  const resolvedHelperText = helperText ?? hint
  const ariaDescribedBy =
    resolvedHelperText || error ? `${selectId}-help` : undefined

  return (
    <Field>
      {label ? (
        <LabelRow>
          <Label htmlFor={selectId}>{label}</Label>
          {tooltip ? (
            <TooltipIcon aria-label={tooltip} data-tooltip={tooltip}>
              i
            </TooltipIcon>
          ) : null}
        </LabelRow>
      ) : null}
      <ControlShell>
        <Control
          id={selectId}
          aria-invalid={Boolean(error)}
          aria-describedby={ariaDescribedBy}
          $hasError={Boolean(error)}
          $isLocked={isLocked}
          disabled={isDisabled}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Control>
        {isLocked ? <LockIcon aria-hidden="true">🔒</LockIcon> : null}
      </ControlShell>
      {(resolvedHelperText || error) && (
        <Helper id={`${selectId}-help`} $hasError={Boolean(error)}>
          {error ?? resolvedHelperText}
        </Helper>
      )}
    </Field>
  )
}
