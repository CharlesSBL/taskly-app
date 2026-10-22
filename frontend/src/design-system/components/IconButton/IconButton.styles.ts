import styled from 'styled-components'
import type { IconButtonSize, IconButtonState } from './IconButton.types'
import {
  iconButtonSizeStyles,
  iconButtonStateStyles,
  iconButtonVariantStyles,
} from './IconButton.variants'

interface BaseIconButtonStyleProps {
  $variant: 'solid' | 'ghost'
  $size: IconButtonSize
  $state: IconButtonState
}

/** Styled primitive used by the public IconButton component. */
export const BaseIconButton = styled.button<BaseIconButtonStyleProps>`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: ${({ theme }) => theme.radii.md};
  cursor: pointer;
  transition: all 0.2s ease;
  color: ${({ theme }) => theme.colors.inkStrong};

  ${({ $variant }) => iconButtonVariantStyles[$variant]}
  ${({ $size }) => iconButtonSizeStyles[$size]}
  ${({ $state }) => iconButtonStateStyles[$state]}

  &:disabled {
    cursor: not-allowed;
  }
`
