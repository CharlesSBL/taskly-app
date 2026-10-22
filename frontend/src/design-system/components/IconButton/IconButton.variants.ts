import { css } from 'styled-components'
import type { IconButtonSize, IconButtonState } from './IconButton.types'

/** Visual styles mapped by icon button variant. */
export const iconButtonVariantStyles = {
  solid: css`
    background: ${({ theme }) => theme.colors.surfaceAlt};
    border: 1px solid ${({ theme }) => theme.colors.border};

    &:hover {
      border-color: ${({ theme }) => theme.colors.primary};
      color: ${({ theme }) => theme.colors.primaryStrong};
    }
  `,
  ghost: css`
    background: transparent;
    border: 1px solid transparent;

    &:hover {
      border-color: ${({ theme }) => theme.colors.primary};
      background: rgba(31, 122, 140, 0.08);
    }
  `,
} as const

/** Visual styles mapped by icon button size. */
export const iconButtonSizeStyles: Record<
  IconButtonSize,
  ReturnType<typeof css>
> = {
  small: css`
    width: 32px;
    height: 32px;
    font-size: 0.95rem;
  `,
  medium: css`
    width: 40px;
    height: 40px;
    font-size: 1.1rem;
  `,
  large: css`
    width: 48px;
    height: 48px;
    font-size: 1.25rem;
  `,
}

/** Visual styles mapped by icon button interaction state. */
export const iconButtonStateStyles: Record<
  IconButtonState,
  ReturnType<typeof css>
> = {
  normal: css`
    opacity: 1;
  `,
  disabled: css`
    opacity: 0.5;
  `,
  locked: css`
    opacity: 0.78;
    background-image: linear-gradient(
      -45deg,
      rgba(255, 255, 255, 0.25) 25%,
      rgba(255, 255, 255, 0.07) 25%,
      rgba(255, 255, 255, 0.07) 50%,
      rgba(255, 255, 255, 0.25) 50%,
      rgba(255, 255, 255, 0.25) 75%,
      rgba(255, 255, 255, 0.07) 75%,
      rgba(255, 255, 255, 0.07) 100%
    );
    background-size: 16px 16px;
  `,
}
