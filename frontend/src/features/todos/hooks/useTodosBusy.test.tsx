import {
  QueryClient,
  QueryClientProvider,
  useMutation,
} from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { expect, it } from 'vitest'
import { todoKeys } from '../api/queryKeys'
import { useTodosBusy } from './useTodosBusy'

function deferred() {
  let resolve!: () => void
  const promise = new Promise<void>((settle) => {
    resolve = settle
  })
  return { promise, resolve }
}

function createClient() {
  return new QueryClient({ defaultOptions: { mutations: { retry: false } } })
}

function createWrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

it('reports no busy state when nothing is in flight', () => {
  const { result } = renderHook(() => useTodosBusy(), {
    wrapper: createWrapper(createClient()),
  })

  expect(result.current).toBe(false)
})

it('is busy while a todo mutation is running and idle again afterwards', async () => {
  const work = deferred()
  const { result } = renderHook(
    () => ({
      busy: useTodosBusy(),
      mutation: useMutation({
        mutationKey: todoKeys.update,
        mutationFn: () => work.promise,
      }),
    }),
    { wrapper: createWrapper(createClient()) },
  )

  act(() => result.current.mutation.mutate())
  await waitFor(() => expect(result.current.busy).toBe(true))

  await act(async () => {
    work.resolve()
    await work.promise
  })
  await waitFor(() => expect(result.current.busy).toBe(false))
})

it('ignores in-flight mutations that do not belong to the todos feature', async () => {
  const work = deferred()
  const { result } = renderHook(
    () => ({
      busy: useTodosBusy(),
      mutation: useMutation({
        mutationKey: ['auth', 'login'],
        mutationFn: () => work.promise,
      }),
    }),
    { wrapper: createWrapper(createClient()) },
  )

  act(() => result.current.mutation.mutate())
  await waitFor(() => expect(result.current.mutation.status).toBe('pending'))

  expect(result.current.busy).toBe(false)

  await act(async () => {
    work.resolve()
    await work.promise
  })
})
