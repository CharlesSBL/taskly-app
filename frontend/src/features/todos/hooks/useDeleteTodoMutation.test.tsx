import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import { request } from '../../../lib/http'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import type { Todo } from '../types'
import { useDeleteTodoMutation } from './useDeleteTodoMutation'

vi.mock('../../../lib/http', () => ({ request: vi.fn() }))

const otherTodo: Todo = { ...todoFixture, id: 3, title: 'Book the room' }

function createClient() {
  return new QueryClient({ defaultOptions: { mutations: { retry: false } } })
}

function createWrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

beforeEach(() => vi.clearAllMocks())

it('removes the deleted task from the cached list', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [todoFixture, otherTodo])
  vi.mocked(request).mockResolvedValue(undefined)
  const { result } = renderHook(() => useDeleteTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(todoFixture.id)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([otherTodo])
  expect(request).toHaveBeenCalledWith(`/todos/${todoFixture.id}`, {
    method: 'DELETE',
  })
})

it('keeps the cached list when the server rejects the deletion', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [todoFixture, otherTodo])
  vi.mocked(request).mockRejectedValue(new Error('Task not found.'))
  const { result } = renderHook(() => useDeleteTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await expect(
      result.current.mutateAsync(todoFixture.id),
    ).rejects.toThrow('Task not found.')
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([
    todoFixture,
    otherTodo,
  ])
})

it('leaves the cache untouched when no list is cached yet', async () => {
  const client = createClient()
  vi.mocked(request).mockResolvedValue(undefined)
  const { result } = renderHook(() => useDeleteTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(todoFixture.id)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toBeUndefined()
})
