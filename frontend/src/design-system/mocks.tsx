import { createElement, type HTMLAttributes } from 'react'
import { vi } from 'vitest'
import type {
  AlertProps,
  BadgeProps,
  ButtonProps,
  CardProps,
  CheckboxGroupProps,
  CheckboxProps,
  DrawerProps,
  HeadingProps,
  IconButtonProps,
  InputProps,
  SelectProps,
  TextProps,
} from './index'

// Import this module from an async vi.mock factory, since vi.mock is hoisted:
// vi.mock('../design-system', () => import('../design-system/mocks'))
// Keep it out of the production barrel; these mocks are only for Vitest.
export { theme } from './theme/theme'

// Strip design-system props while preserving native attributes and callbacks.
const designProps = new Set([
  'variant',
  'size',
  'state',
  'fullWidth',
  'lockedIcon',
  'muted',
  'preserveWhitespace',
  'completed',
  'level',
  'as',
  'label',
  'hint',
  'helperText',
  'error',
  'tooltip',
  'multiline',
  'options',
])

function nativeProps(props: object) {
  return Object.fromEntries(
    Object.entries(props).filter(([key]) => !designProps.has(key)),
  )
}

export const GlobalStyles = vi.fn(() => null)

export const AppHeader = vi.fn((props: HTMLAttributes<HTMLElement>) => (
  <header {...props} />
))

export const Heading = vi.fn((props: HeadingProps) =>
  createElement(`h${props.level ?? 1}`, nativeProps(props)),
)

export const Text = vi.fn((props: TextProps) =>
  createElement(props.as ?? 'p', nativeProps(props)),
)

export const Alert = vi.fn((props: AlertProps) => (
  <div data-testid="alert" {...nativeProps(props)} />
))

export const Badge = vi.fn((props: BadgeProps) => (
  <span {...nativeProps(props)} />
))

export const Card = vi.fn((props: CardProps) => <div {...nativeProps(props)} />)

export const Button = vi.fn((props: ButtonProps) => (
  <button {...nativeProps(props)} />
))

export const IconButton = vi.fn((props: IconButtonProps) => (
  <button {...nativeProps(props)} />
))

export const Input = vi.fn((props: InputProps) => (
  <label>
    {props.label}
    {props.multiline ? (
      <textarea {...nativeProps(props)} />
    ) : (
      <input {...nativeProps(props)} />
    )}
    {props.error && <span>{props.error}</span>}
  </label>
))

export const Select = vi.fn((props: SelectProps) => (
  <label>
    {props.label}
    <select {...nativeProps(props)}>
      {props.options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
    {props.error && <span>{props.error}</span>}
  </label>
))

export const Checkbox = vi.fn((props: CheckboxProps) => (
  <label>
    <input {...nativeProps(props)} type="checkbox" />
    {props.label}
  </label>
))

export const CheckboxGroup = vi.fn(
  ({
    label,
    options,
    value,
    onChange,
    disabled,
    error,
  }: CheckboxGroupProps) => (
    <fieldset disabled={disabled}>
      <legend>{label}</legend>
      {options.map((option) => (
        <label key={option}>
          <input
            type="checkbox"
            checked={value.includes(option)}
            onChange={(event) =>
              onChange(
                event.target.checked
                  ? [...value, option]
                  : value.filter((item) => item !== option),
              )
            }
          />
          {option}
        </label>
      ))}
      {error && <span>{error}</span>}
    </fieldset>
  ),
)

export const Drawer = vi.fn(
  ({ title, isOpen, onClose, children, busy }: DrawerProps) =>
    isOpen ? (
      <div role="dialog" aria-label={title}>
        <button type="button" disabled={busy} onClick={onClose}>
          Close
        </button>
        {children}
      </div>
    ) : null,
)
