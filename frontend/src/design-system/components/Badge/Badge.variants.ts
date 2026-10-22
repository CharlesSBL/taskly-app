import { css } from 'styled-components'
import type { BadgeVariant } from './Badge.types'

/** Visual styles mapped by badge variant. */
export const badgeVariantStyles: Record<
  BadgeVariant,
  ReturnType<typeof css>
> = {
  neutral: css`
    background: ${({ theme }) => theme.colors.surfaceAlt};
    color: ${({ theme }) => theme.colors.inkStrong};
  `,
  info: css`
    background: rgba(60, 90, 137, 0.15);
    color: ${({ theme }) => theme.colors.info};
  `,
  success: css`
    background: rgba(46, 139, 87, 0.16);
    color: ${({ theme }) => theme.colors.success};
  `,
  warning: css`
    background: rgba(180, 71, 27, 0.15);
    color: ${({ theme }) => theme.colors.warning};
  `,
}
