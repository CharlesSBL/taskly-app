import { css } from 'styled-components'
import type { ButtonSize, ButtonState, ButtonVariant } from './Button.types'

/** Visual styles mapped by button variant. */
export const buttonVariantStyles: Record<
  ButtonVariant,
  ReturnType<typeof css>
> = {
  primary: css`
    background: ${({ theme }) => theme.colors.primary};
    color: #fff;

    &:hover {
      background: ${({ theme }) => theme.colors.primaryStrong};
    }
  `,
  secondary: css`
    background: ${({ theme }) => theme.colors.surfaceAlt};
    color: ${({ theme }) => theme.colors.inkStrong};
    border: 1px solid ${({ theme }) => theme.colors.border};

    &:hover {
      border-color: ${({ theme }) => theme.colors.primary};
      color: ${({ theme }) => theme.colors.primaryStrong};
    }
  `,
  danger: css`
    background: ${({ theme }) => theme.colors.warning};
    color: ${({ theme }) => theme.colors.surface};

    &:hover {
      filter: brightness(0.9);
    }
  `,
  ghost: css`
    background: transparent;
    color: ${({ theme }) => theme.colors.primaryStrong};
    border: 1px solid transparent;

    &:hover {
      border-color: ${({ theme }) => theme.colors.primary};
      background: rgba(31, 122, 140, 0.08);
    }
  `,
}

/** Visual styles mapped by button size. */
export const buttonSizeStyles: Record<ButtonSize, ReturnType<typeof css>> = {
  small: css`
    padding: 8px 14px;
    font-size: 0.85rem;
  `,
  medium: css`
    padding: 10px 18px;
    font-size: 0.95rem;
  `,
  large: css`
    padding: 13px 22px;
    font-size: 1rem;
  `,
}

/** Visual styles mapped by button interaction state. */
export const buttonStateStyles: Record<ButtonState, ReturnType<typeof css>> = {
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
      rgba(255, 255, 255, 0.2) 25%,
      rgba(255, 255, 255, 0.05) 25%,
      rgba(255, 255, 255, 0.05) 50%,
      rgba(255, 255, 255, 0.2) 50%,
      rgba(255, 255, 255, 0.2) 75%,
      rgba(255, 255, 255, 0.05) 75%,
      rgba(255, 255, 255, 0.05) 100%
    );
    background-size: 16px 16px;
  `,
}
