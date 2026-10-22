import { createGlobalStyle } from 'styled-components'

export const GlobalStyles = createGlobalStyle`
  :root {
    --space-xs: ${({ theme }) => theme.spacing.xs};
    --space-sm: ${({ theme }) => theme.spacing.sm};
    --space-md: ${({ theme }) => theme.spacing.md};
    --space-lg: ${({ theme }) => theme.spacing.lg};
    --space-xl: ${({ theme }) => theme.spacing.xl};
    --space-xxl: ${({ theme }) => theme.spacing.xxl};
    --layout-content: ${({ theme }) => theme.layout.content};
  }

  *,
  *::before,
  *::after {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    min-height: 100vh;
    font-family: ${({ theme }) => theme.typography.body};
    color: ${({ theme }) => theme.colors.ink};
    font-size: ${({ theme }) => theme.typography.sizes.body};
    line-height: ${({ theme }) => theme.typography.lineHeight};
    background: ${({ theme }) => theme.colors.surfaceAlt};
  }

  h1,
  h2,
  h3,
  h4,
  h5 {
    font-family: ${({ theme }) => theme.typography.heading};
    color: ${({ theme }) => theme.colors.inkStrong};
    margin: 0;
  }

  p {
    margin: 0;
  }

  a {
    color: inherit;
    text-decoration: none;
  }

  button,
  input,
  textarea,
  select {
    font-family: ${({ theme }) => theme.typography.body};
  }

  :focus-visible {
    outline: 3px solid ${({ theme }) => theme.colors.primary};
    outline-offset: 2px;
  }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation: none !important;
      transition: none !important;
    }
  }
`
