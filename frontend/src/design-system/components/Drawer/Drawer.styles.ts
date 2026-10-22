import styled from 'styled-components'

/** Native modal surface provides focus containment and an inert background. */
export const Overlay = styled.dialog`
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100dvh;
  max-width: none;
  max-height: none;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: ${({ theme }) => theme.colors.ink};

  &::backdrop {
    background: ${({ theme }) => theme.colors.overlay};
  }
`

export const Panel = styled.div`
  margin-left: auto;
  height: 100%;
  width: min(${({ theme }) => theme.layout.drawer}, 100%);
  background: ${({ theme }) => theme.colors.surface};
  box-shadow: ${({ theme }) => theme.shadows.raised};
  padding: ${({ theme }) => theme.spacing.lg};
  display: flex;
  flex-direction: column;
  gap: ${({ theme }) => theme.spacing.lg};
  overflow-y: auto;
`

export const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.md};
`

export const Content = styled.div`
  display: grid;
  gap: ${({ theme }) => theme.spacing.md};
`
