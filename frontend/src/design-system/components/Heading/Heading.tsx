import { BaseHeading } from './Heading.styles'
import type { HeadingProps } from './Heading.types'

export function Heading({
  level = 1,
  completed = false,
  ...props
}: HeadingProps) {
  return (
    <BaseHeading
      as={`h${level}`}
      $level={level}
      $completed={completed}
      {...props}
    />
  )
}
