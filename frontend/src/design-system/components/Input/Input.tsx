import { useId } from 'react'
import type { InputProps } from './Input.types'
import {
  Control,
  ControlShell,
  Field,
  Helper,
  Label,
  LabelRow,
  LockIcon,
  Textarea,
  TooltipIcon,
} from './Input.styles'

/**
 * Text input or textarea field with label, helper/error text, tooltip, and locked state support.
 */
export function Input({
  label,
  hint,
  helperText,
  error,
  tooltip,
  state = 'normal',
  multiline = false,
  rows = 4,
  id,
  disabled,
  ...props
}: InputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId
  const resolvedState = disabled ? 'disabled' : state
  const isLocked = resolvedState === 'locked'
  const isDisabled = resolvedState === 'disabled' || isLocked
  const resolvedHelperText = helperText ?? hint
  const ariaDescribedBy =
    resolvedHelperText || error ? `${inputId}-help` : undefined

  return (
    <Field>
      {label ? (
        <LabelRow>
          <Label htmlFor={inputId}>{label}</Label>
          {tooltip ? (
            <TooltipIcon aria-label={tooltip} data-tooltip={tooltip}>
              i
            </TooltipIcon>
          ) : null}
        </LabelRow>
      ) : null}
      <ControlShell>
        {multiline ? (
          <Textarea
            id={inputId}
            rows={rows}
            aria-invalid={Boolean(error)}
            aria-describedby={ariaDescribedBy}
            $hasError={Boolean(error)}
            $isLocked={isLocked}
            disabled={isDisabled}
            readOnly={isLocked}
            {...props}
          />
        ) : (
          <Control
            id={inputId}
            aria-invalid={Boolean(error)}
            aria-describedby={ariaDescribedBy}
            $hasError={Boolean(error)}
            $isLocked={isLocked}
            disabled={isDisabled}
            readOnly={isLocked}
            {...props}
          />
        )}
        {isLocked ? <LockIcon aria-hidden="true">🔒</LockIcon> : null}
      </ControlShell>
      {(resolvedHelperText || error) && (
        <Helper id={`${inputId}-help`} $hasError={Boolean(error)}>
          {error ?? resolvedHelperText}
        </Helper>
      )}
    </Field>
  )
}
