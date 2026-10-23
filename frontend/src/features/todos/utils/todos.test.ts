import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Todo, TodoInput } from '../types'
import { formatDate, isOverdue, selectTodos, validateTodo } from './todos'

const base: Todo = {
  id: 1,
  title: 'Sprint plan',
  description: '',
  priority: 'medium',
  completed: false,
  due_date: null,
  created_at: '2026-10-01T12:00:00Z',
  updated_at: '2026-10-01T12:00:00Z',
}

function makeInput(overrides: Partial<TodoInput> = {}): TodoInput {
  return {
    title: 'Plan the sprint',
    description: '',
    priority: 'medium',
    due_date: null,
    completed: false,
    ...overrides,
  }
}

afterEach(() => {
  vi.useRealTimers()
})

describe('selectTodos', () => {
  it('combines status with a case-insensitive search in the description', () => {
    const matching = { ...base, description: 'Discuss the API' }
    const todos = [
      matching,
      { ...matching, id: 2, completed: true },
      { ...base, id: 3 },
    ]
    expect(selectTodos(todos, 'active', ' api ', 'newest')).toEqual([matching])
  })

  it('sorts by priority without changing the source array', () => {
    const high: Todo = { ...base, id: 2, priority: 'high' }
    const todos = [base, high]
    expect(selectTodos(todos, 'all', '', 'priority')).toEqual([high, base])
    expect(todos).toEqual([base, high])
  })

  it('keeps only completed tasks for the completed filter', () => {
    const done: Todo = { ...base, id: 2, completed: true }
    expect(selectTodos([base, done], 'completed', '', 'newest')).toEqual([done])
  })

  it('orders by due date with undated tasks last', () => {
    const noDate: Todo = { ...base, id: 2, due_date: null }
    const late: Todo = { ...base, id: 3, due_date: '2026-12-24' }
    const soon: Todo = { ...base, id: 4, due_date: '2026-10-05' }

    expect(selectTodos([noDate, late, soon], 'all', '', 'due')).toEqual([
      soon,
      late,
      noDate,
    ])
  })

  it('breaks ties on the newest sort by the higher id', () => {
    const first: Todo = { ...base, id: 2 }
    const second: Todo = { ...base, id: 9 }

    expect(selectTodos([first, second], 'all', '', 'newest')).toEqual([
      second,
      first,
    ])
  })

  it('returns an empty list when the search matches nothing', () => {
    expect(selectTodos([base], 'all', 'release notes', 'newest')).toEqual([])
  })
})

describe('validateTodo', () => {
  it('accepts a valid task', () => {
    expect(validateTodo(makeInput({ due_date: '2026-12-31' }))).toEqual({})
  })

  it.each(['', '   '])('rejects the blank title %j', (title) => {
    expect(validateTodo(makeInput({ title }))).toEqual({
      title: 'Enter a task title.',
    })
  })

  it('accepts a title of exactly 120 characters', () => {
    expect(validateTodo(makeInput({ title: 'a'.repeat(120) }))).toEqual({})
  })

  it('rejects a title longer than 120 characters', () => {
    expect(validateTodo(makeInput({ title: 'a'.repeat(121) }))).toEqual({
      title: 'The title must be at most 120 characters.',
    })
  })

  it('accepts a description of exactly 2000 characters', () => {
    expect(validateTodo(makeInput({ description: 'a'.repeat(2000) }))).toEqual(
      {},
    )
  })

  it('rejects a description longer than 2000 characters', () => {
    expect(validateTodo(makeInput({ description: 'a'.repeat(2001) }))).toEqual({
      description: 'The description must be at most 2000 characters.',
    })
  })

  it.each(['2026-13-01', '2026-02-30', '31/12/2026'])(
    'rejects the invalid due date %s',
    (due_date) => {
      expect(validateTodo(makeInput({ due_date }))).toEqual({
        due_date: 'Enter a valid date.',
      })
    },
  )

  it('reports every invalid field at once', () => {
    expect(
      validateTodo(
        makeInput({ title: ' ', description: 'a'.repeat(2001), due_date: 'x' }),
      ),
    ).toEqual({
      title: 'Enter a task title.',
      description: 'The description must be at most 2000 characters.',
      due_date: 'Enter a valid date.',
    })
  })
})

describe('isOverdue', () => {
  it('reports an unfinished task due before today as overdue', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-15T09:00:00'))

    expect(isOverdue({ ...base, due_date: '2026-10-14' })).toBe(true)
  })

  it('does not report a task due today or later as overdue', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-15T09:00:00'))

    expect(isOverdue({ ...base, due_date: '2026-10-15' })).toBe(false)
    expect(isOverdue({ ...base, due_date: '2026-10-16' })).toBe(false)
  })

  it('never reports a completed task as overdue', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-15T09:00:00'))

    expect(isOverdue({ ...base, completed: true, due_date: '2026-10-14' })).toBe(
      false,
    )
  })

  it('does not report a task without a due date as overdue', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-15T09:00:00'))

    expect(isOverdue({ ...base, due_date: null })).toBe(false)
  })
})

describe('formatDate', () => {
  it('formats an ISO date as a readable British date', () => {
    expect(formatDate('2026-10-01')).toBe('1 Oct 2026')
  })
})
