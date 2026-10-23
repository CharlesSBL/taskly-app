import { beforeEach, expect, it, vi } from 'vitest'
import { request } from '../../../lib/http'
import { todoFixture } from '../../../test/todoFixture'
import { todosApi } from './todos'

vi.mock('../../../lib/http', () => ({ request: vi.fn() }))
beforeEach(() => vi.clearAllMocks())

it('passes the abort signal when fetching tasks', async () => {
  const signal = new AbortController().signal
  vi.mocked(request).mockResolvedValue([todoFixture])
  await expect(todosApi.list(signal)).resolves.toEqual([todoFixture])
  expect(request).toHaveBeenCalledWith('/todos', { signal })
})

it('requests due-soon tasks with an explicit window and signal', async () => {
  const signal = new AbortController().signal
  vi.mocked(request).mockResolvedValue([todoFixture])
  await expect(todosApi.listDueSoon(7, signal)).resolves.toEqual([todoFixture])
  expect(request).toHaveBeenCalledWith('/todos/due-soon?days=7', { signal })
})

it('defaults the due-soon window to three days', async () => {
  vi.mocked(request).mockResolvedValue([todoFixture])
  await expect(todosApi.listDueSoon()).resolves.toEqual([todoFixture])
  expect(request).toHaveBeenCalledWith('/todos/due-soon?days=3', {
    signal: undefined,
  })
})

it('sends only writable task fields on creation', async () => {
  vi.mocked(request).mockResolvedValue(todoFixture)
  await expect(todosApi.create(todoFixture)).resolves.toEqual(todoFixture)
  expect(request).toHaveBeenCalledWith('/todos', {
    method: 'POST',
    body: JSON.stringify({
      title: todoFixture.title,
      description: '',
      priority: 'medium',
      due_date: null,
      completed: false,
    }),
  })
})
