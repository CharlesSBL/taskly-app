import styled from 'styled-components'
import type { BadgeVariant } from './Badge.types'
import { badgeVariantStyles } from './Badge.variants'

interface BaseBadgeStyleProps {
  $variant: BadgeVariant
}

/** Styled primitive used by the public Badge component. */
export const BaseBadge = styled.span<BaseBadgeStyleProps>`
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: ${({ theme }) => theme.radii.pill};
  font-size: 0.8rem;
  font-weight: 600;

  ${({ $variant }) => badgeVariantStyles[$variant]}
`
