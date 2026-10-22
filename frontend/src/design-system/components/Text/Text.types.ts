import type { HTMLAttributes } from 'react'

export interface TextProps extends HTMLAttributes<HTMLParagraphElement> {
  as?: 'p' | 'span'
  muted?: boolean
  size?: 'small' | 'body'
  preserveWhitespace?: boolean
}
