export const theme = {
  colors: {
    inkStrong: '#12212b',
    ink: '#2a3a45',
    inkMuted: '#5e6c76',
    surface: '#ffffff',
    surfaceAlt: '#f5f4f0',
    border: '#d6dde1',
    primary: '#1f7a8c',
    primaryStrong: '#155c69',
    accent: '#e38b2c',
    accentSoft: '#f9e6cf',
    success: '#2e8b57',
    warning: '#b4471b',
    info: '#3c5a89',
    shadow: 'rgba(18, 33, 43, 0.12)',
    overlay: 'rgba(9, 12, 16, 0.4)',
  },
  layout: {
    content: '960px',
    drawer: '420px',
    mobile: '640px',
    tablet: '960px',
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px',
  },
  radii: {
    sm: '8px',
    md: '12px',
    lg: '20px',
    pill: '999px',
  },
  typography: {
    body: '"Source Sans 3", "Segoe UI", sans-serif',
    heading: '"Space Grotesk", "Segoe UI", sans-serif',
    sizes: {
      small: '0.85rem',
      body: '1rem',
      h1: '2rem',
      h2: '1.5rem',
      h3: '1.125rem',
    },
    lineHeight: 1.5,
  },
  shadows: {
    card: '0 16px 32px -24px rgba(18, 33, 43, 0.45)',
    raised: '0 20px 40px -28px rgba(18, 33, 43, 0.55)',
  },
}

export type Theme = typeof theme
