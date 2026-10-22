import { BaseText } from './Text.styles'
import type { TextProps } from './Text.types'

export function Text({
  muted = false,
  size = 'body',
  preserveWhitespace = false,
  ...props
}: TextProps) {
  return (
    <BaseText
      $muted={muted}
      $size={size}
      $preserveWhitespace={preserveWhitespace}
      {...props}
    />
  )
}
