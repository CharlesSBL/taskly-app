import { act, renderHook } from '@testing-library/react'
import { expect, it } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import type { Todo } from '../types'
import { useTodoFilters } from './useTodoFilters'

const activeTodo: Todo = {
  ...todoFixture,
  id: 1,
  title: 'Write release notes',
  priority: 'low',
  created_at: '2026-10-01T12:00:00Z',
  updated_at: '2026-10-01T12:00:00Z',
}

const completedTodo: Todo = {
  ...todoFixture,
  id: 2,
  title: 'Archive the release notes',
  description: 'Published last week',
  priority: 'high',
  completed: true,
  created_at: '2026-10-02T12:00:00Z',
  updated_at: '2026-10-02T12:00:00Z',
}

const todos = [activeTodo, completedTodo]

it('starts with no filtering, no search and the newest task first', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  expect(result.current.filter).toBe('all')
  expect(result.current.search).toBe('')
  expect(result.current.sort).toBe('newest')
  expect(result.current.visible).toEqual([completedTodo, activeTodo])
})

it('exposes only completed tasks once the filter changes', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setFilter('completed'))

  expect(result.current.filter).toBe('completed')
  expect(result.current.visible).toEqual([completedTodo])
})

it('exposes only active tasks for the active filter', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setFilter('active'))

  expect(result.current.visible).toEqual([activeTodo])
})

it('matches the search term against the title case-insensitively', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setSearch('  ARCHIVE  '))

  expect(result.current.search).toBe('  ARCHIVE  ')
  expect(result.current.visible).toEqual([completedTodo])
})

it('orders the visible tasks by priority once the sort changes', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setSort('priority'))

  expect(result.current.sort).toBe('priority')
  expect(result.current.visible).toEqual([completedTodo, activeTodo])
})

it('recomputes the visible tasks when the task list changes', () => {
  const { result, rerender } = renderHook(
    ({ list }: { list: Todo[] }) => useTodoFilters(list),
    { initialProps: { list: todos } },
  )

  rerender({ list: [activeTodo] })

  expect(result.current.visible).toEqual([activeTodo])
})

it('reports no visible tasks for a search that matches nothing', () => {
  const { result } = renderHook(() => useTodoFilters(todos))

  act(() => result.current.setSearch('nothing resembles this'))

  expect(result.current.visible).toEqual([])
})
