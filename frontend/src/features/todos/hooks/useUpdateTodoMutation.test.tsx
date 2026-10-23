import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, expect, it, vi } from 'vitest'
import { request } from '../../../lib/http'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import type { Todo } from '../types'
import { useUpdateTodoMutation } from './useUpdateTodoMutation'

vi.mock('../../../lib/http', () => ({ request: vi.fn() }))

const otherTodo: Todo = { ...todoFixture, id: 3, title: 'Book the room' }
const complete = { id: todoFixture.id, input: { completed: true } }
const rename = { id: todoFixture.id, input: { title: 'Renamed' } }
const blankTitle = { id: todoFixture.id, input: { title: '' } }

function createClient() {
  return new QueryClient({ defaultOptions: { mutations: { retry: false } } })
}

function createWrapper(client: QueryClient) {
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  )
}

beforeEach(() => vi.clearAllMocks())

it('replaces the edited task in the cached list and keeps the others', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [todoFixture, otherTodo])
  const saved: Todo = { ...todoFixture, completed: true }
  vi.mocked(request).mockResolvedValue(saved)
  const { result } = renderHook(() => useUpdateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(complete)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([saved, otherTodo])
  expect(request).toHaveBeenCalledWith(`/todos/${todoFixture.id}`, {
    method: 'PATCH',
    body: JSON.stringify({ completed: true }),
  })
})

it('sends only the field that changed', async () => {
  const client = createClient()
  vi.mocked(request).mockResolvedValue({ ...todoFixture, title: 'Renamed' })
  const { result } = renderHook(() => useUpdateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(rename)
  })

  const [, init] = vi.mocked(request).mock.calls[0]
  expect(JSON.parse(String(init?.body))).toEqual({ title: 'Renamed' })
})

it('keeps the cached list when the server rejects the update', async () => {
  const client = createClient()
  client.setQueryData<Todo[]>(todoKeys.list, [todoFixture, otherTodo])
  vi.mocked(request).mockRejectedValue(new Error('The title is invalid.'))
  const { result } = renderHook(() => useUpdateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await expect(result.current.mutateAsync(blankTitle)).rejects.toThrow(
      'The title is invalid.',
    )
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toEqual([
    todoFixture,
    otherTodo,
  ])
})

it('leaves the cache untouched when no list is cached yet', async () => {
  const client = createClient()
  vi.mocked(request).mockResolvedValue({ ...todoFixture, completed: true })
  const { result } = renderHook(() => useUpdateTodoMutation(), {
    wrapper: createWrapper(client),
  })

  await act(async () => {
    await result.current.mutateAsync(complete)
  })

  expect(client.getQueryData<Todo[]>(todoKeys.list)).toBeUndefined()
})
