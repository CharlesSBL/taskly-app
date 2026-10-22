import styled from 'styled-components'

export const BaseText = styled.p<{
  $muted: boolean
  $size: 'small' | 'body'
  $preserveWhitespace: boolean
}>`
  margin: 0;
  font-family: ${({ theme }) => theme.typography.body};
  font-size: ${({ theme, $size }) => theme.typography.sizes[$size]};
  line-height: ${({ theme }) => theme.typography.lineHeight};
  color: ${({ theme, $muted }) => ($muted ? theme.colors.inkMuted : theme.colors.ink)};
  white-space: ${({ $preserveWhitespace }) => ($preserveWhitespace ? 'pre-wrap' : 'normal')};
  overflow-wrap: anywhere;
`
