import styled from 'styled-components'

/** Inline wrapper for checkbox and label. */
export const Wrapper = styled.label`
  position: relative;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: ${({ theme }) => theme.spacing.sm};
`

/** Native checkbox visually hidden but still accessible. */
export const HiddenInput = styled.input`
  position: absolute;
  opacity: 0;

  &:focus-visible + span {
    outline: 3px solid rgba(31, 122, 140, 0.2);
    outline-offset: 2px;
  }

  &:checked + span {
    background: ${({ theme }) => theme.colors.primary};
    border-color: ${({ theme }) => theme.colors.primaryStrong};
  }

  &:checked + span::after {
    opacity: 1;
  }
`

/** Visual checkbox square synced with hidden input state. */
export const Box = styled.span`
  width: 18px;
  height: 18px;
  border-radius: 6px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  background: #fff;
  position: relative;

  &::after {
    content: '';
    width: 8px;
    height: 8px;
    background: #fff;
    border-radius: 2px;
    opacity: 0;
    transition: opacity 0.2s ease;
  }
`

/** Label text linked to the hidden checkbox input. */
export const Label = styled.span`
  font-size: 0.95rem;
  color: ${({ theme }) => theme.colors.inkStrong};
`
