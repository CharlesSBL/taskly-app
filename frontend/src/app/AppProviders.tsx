import type { ReactNode } from 'react'
import { QueryClientProvider, type QueryClient } from '@tanstack/react-query'
import { ThemeProvider } from 'styled-components'
import { GlobalStyles, theme } from '../design-system'
import { queryClient } from '../lib/queryClient'

export function AppProviders({
  children,
  client = queryClient,
}: {
  children: ReactNode
  client?: QueryClient
}) {
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider theme={theme}>
        <GlobalStyles />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  )
}
