import styled from 'styled-components'

export const BaseHeading = styled.h1<{
  $level: 1 | 2 | 3
  $completed: boolean
}>`
  margin: 0;
  font-family: ${({ theme }) => theme.typography.heading};
  font-size: ${({ theme, $level }) => theme.typography.sizes[`h${$level}`]};
  font-weight: 600;
  line-height: ${({ theme }) => theme.typography.lineHeight};
  color: ${({ theme, $completed }) => ($completed ? theme.colors.inkMuted : theme.colors.inkStrong)};
  text-decoration: ${({ $completed }) => ($completed ? 'line-through' : 'none')};
  overflow-wrap: anywhere;
`
