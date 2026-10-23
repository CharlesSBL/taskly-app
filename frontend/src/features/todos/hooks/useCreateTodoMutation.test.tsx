import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import { request } from '../../../lib/http'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import type { Todo, TodoInput } from '../types'
import { useCreateTodoMutation } from './useCreateTodoMutation'

vi.mock('../../../lib/http', () => ({ request: vi.fn() }))

const input: TodoInput = {
  title: 'Prepare a demo',
  description: '',
  priority: 'medium',
  due_date: null,
  completed: false,
}

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

it('prepends the created task to the cached list', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [otherTodo])
  vi.mocked(request).mockResolvedValue(todoFixture)
  const { result } = renderHook(() => useCreateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(input)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([
    todoFixture,
    otherTodo,
  ])
})

it('replaces a cached task with the same id instead of duplicating it', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [
    { ...todoFixture, title: 'Stale title' },
    otherTodo,
  ])
  vi.mocked(request).mockResolvedValue(todoFixture)
  const { result } = renderHook(() => useCreateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(input)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([
    todoFixture,
    otherTodo,
  ])
})

it('starts the cached list when no list is cached yet', async () => {
  const client = createClient()
  vi.mocked(request).mockResolvedValue(todoFixture)
  const { result } = renderHook(() => useCreateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(input)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([todoFixture])
})

it('keeps the cached list when the server rejects the creation', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [otherTodo])
  vi.mocked(request).mockRejectedValue(new Error('The title is invalid.'))
  const { result } = renderHook(() => useCreateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await expect(result.current.mutateAsync(input)).rejects.toThrow(
      'The title is invalid.',
    )
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([otherTodo])
})
