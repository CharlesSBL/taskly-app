import { Checkbox } from '../Checkbox'
import type { CheckboxGroupProps } from './CheckboxGroup.types'
import {
  Group,
  Helper,
  Label,
  LabelRow,
  List,
  TooltipIcon,
} from './CheckboxGroup.styles'

/**
 * Checkbox group with optional helper/error text and label tooltip.
 */
export function CheckboxGroup({
  label,
  tooltip,
  options,
  value,
  onChange,
  helper,
  error,
  disabled = false,
}: CheckboxGroupProps) {
  return (
    <Group>
      <LabelRow>
        <Label>{label}</Label>
        {tooltip ? (
          <TooltipIcon aria-label={tooltip} data-tooltip={tooltip}>
            i
          </TooltipIcon>
        ) : null}
      </LabelRow>
      <List>
        {options.map((option) => {
          const checked = value.includes(option)
          return (
            <Checkbox
              key={option}
              label={option}
              checked={checked}
              disabled={disabled}
              onChange={() => {
                const next = checked
                  ? value.filter((item) => item !== option)
                  : [...value, option]
                onChange(next)
              }}
            />
          )
        })}
      </List>
      {error ? <Helper $hasError>{error}</Helper> : null}
      {!error && helper ? <Helper>{helper}</Helper> : null}
    </Group>
  )
}
