import styled from 'styled-components'
import type { AlertVariant } from './Alert.types'

export const BaseAlert = styled.div<{ $variant: AlertVariant }>`
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: ${({ theme }) => theme.spacing.md};
  padding: ${({ theme }) => theme.spacing.md};
  border: 1px solid ${({ theme, $variant }) => theme.colors[$variant]};
  border-radius: ${({ theme }) => theme.radii.md};
  background: ${({ theme }) => theme.colors.surface};
  color: ${({ theme, $variant }) => theme.colors[$variant]};
  font-family: ${({ theme }) => theme.typography.body};
  font-size: ${({ theme }) => theme.typography.sizes.body};
  line-height: ${({ theme }) => theme.typography.lineHeight};
  overflow-wrap: anywhere;
`
