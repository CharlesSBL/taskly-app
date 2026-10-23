import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import { request } from '../../../lib/http'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { useTodosQuery } from './useTodosQuery'

vi.mock('../../../lib/http', () => ({ request: vi.fn() }))

function createClient() {
  return new QueryClient({ defaultOptions: { queries: { retry: false } } })
}

function createWrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

beforeEach(() => vi.clearAllMocks())

it('loads the task list through the api with an abort signal', async () => {
  vi.mocked(request).mockResolvedValue([todoFixture])
  const { result } = renderHook(() => useTodosQuery(), {
    wrapper: createWrapper(createClient()),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))

  expect(result.current.data).toEqual([todoFixture])
  const [path, init] = vi.mocked(request).mock.calls[0]
  expect(path).toBe('/todos')
  expect(init?.signal).toBeInstanceOf(AbortSignal)
})

it('stores the loaded tasks in the cache under the list key', async () => {
  const client = createClient()
  vi.mocked(request).mockResolvedValue([todoFixture])
  const { result } = renderHook(() => useTodosQuery(), {
    wrapper: createWrapper(client),
  })

  await waitFor(() => expect(result.current.isSuccess).toBe(true))

  expect(client.getQueryData(todoKeys.list)).toEqual([todoFixture])
})

it('exposes the request failure so the page can show it', async () => {
  vi.mocked(request).mockRejectedValue(
    new Error('Cannot connect to the server. Please try again.'),
  )
  const { result } = renderHook(() => useTodosQuery(), {
    wrapper: createWrapper(createClient()),
  })

  await waitFor(() => expect(result.current.isError).toBe(true))

  expect(result.current.data).toBeUndefined()
  expect(result.current.error?.message).toBe(
    'Cannot connect to the server. Please try again.',
  )
})
