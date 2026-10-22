import type { Preview } from '@storybook/react-vite'
import { ThemeProvider } from 'styled-components'
import { GlobalStyles, theme } from '../src/design-system'

const preview: Preview = {
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <GlobalStyles />
        <Story />
      </ThemeProvider>
    ),
  ],
}

export default preview
