import { QueryClient, useQueryClient } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { useTheme } from 'styled-components'
import { beforeEach, expect, it, vi } from 'vitest'
import { theme } from '../design-system'
import { queryClient } from '../lib/queryClient'
import { AppProviders } from './AppProviders'

vi.mock('../design-system', () => import('../design-system/mocks'))

let providedClient: QueryClient | undefined

function ClientProbe() {
  providedClient = useQueryClient()
  return null
}

function ThemeProbe() {
  const activeTheme = useTheme()
  return <p>{activeTheme.colors.primary}</p>
}

beforeEach(() => {
  providedClient = undefined
  vi.clearAllMocks()
})

it('renders its children inside the providers', () => {
  render(
    <AppProviders>
      <p>Tasks page</p>
    </AppProviders>,
  )

  expect(screen.getByText('Tasks page')).toBeVisible()
})

it('provides the shared query client by default', () => {
  render(
    <AppProviders>
      <ClientProbe />
    </AppProviders>,
  )

  expect(providedClient).toBe(queryClient)
})

it('provides an injected query client instead of the shared one', () => {
  const client = new QueryClient()

  render(
    <AppProviders client={client}>
      <ClientProbe />
    </AppProviders>,
  )

  expect(providedClient).toBe(client)
})

it('provides the design-system theme to descendants', () => {
  render(
    <AppProviders>
      <ThemeProbe />
    </AppProviders>,
  )

  expect(screen.getByText(theme.colors.primary)).toBeVisible()
})
