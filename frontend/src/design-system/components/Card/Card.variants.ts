import { css } from 'styled-components'
import type { CardVariant } from './Card.types'

/** Visual styles mapped by card variant. */
export const cardVariantStyles: Record<CardVariant, ReturnType<typeof css>> = {
  outline: css`
    border: 1px solid ${({ theme }) => theme.colors.border};
    background: ${({ theme }) => theme.colors.surface};
  `,
  elevated: css`
    border: 1px solid transparent;
    background: ${({ theme }) => theme.colors.surface};
    box-shadow: ${({ theme }) => theme.shadows.card};
  `,
}
