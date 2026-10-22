import styled from 'styled-components'
import type { ButtonSize, ButtonState, ButtonVariant } from './Button.types'
import {
  buttonSizeStyles,
  buttonStateStyles,
  buttonVariantStyles,
} from './Button.variants'

interface BaseButtonStyleProps {
  $variant: ButtonVariant
  $size: ButtonSize
  $state: ButtonState
  $fullWidth?: boolean
}

/** Styled primitive used by the public Button component. */
export const BaseButton = styled.button<BaseButtonStyleProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${({ theme }) => theme.spacing.sm};
  border-radius: ${({ theme }) => theme.radii.pill};
  border: 1px solid transparent;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  width: ${({ $fullWidth }) => ($fullWidth ? '100%' : 'auto')};

  ${({ $variant }) => buttonVariantStyles[$variant]}
  ${({ $size }) => buttonSizeStyles[$size]}
  ${({ $state }) => buttonStateStyles[$state]}

  &:disabled {
    cursor: not-allowed;
  }
`
