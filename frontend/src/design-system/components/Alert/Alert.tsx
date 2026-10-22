import { BaseAlert } from './Alert.styles'
import type { AlertProps } from './Alert.types'

export function Alert({ variant = 'info', role, ...props }: AlertProps) {
  return (
    <BaseAlert
      $variant={variant}
      role={role ?? (variant === 'warning' ? 'alert' : 'status')}
      {...props}
    />
  )
}
