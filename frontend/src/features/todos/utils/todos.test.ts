import { describe, expect, it, vi } from 'vitest'
import { formatDate, isOverdue, selectTodos, validateTodo } from './todos'
import type { Todo, TodoInput } from '../types'

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

const validInput: TodoInput = {
  title: 'Sprint plan',
  description: 'Discuss the API',
  priority: 'high',
  due_date: null,
  completed: false,
}

const malformedDates = ['2026-02-30', '10/01/2026', '2026-13-01', '2026-1-5']

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

  it('matches the search against the title', () => {
    const matching = { ...base, title: 'Write the release notes' }
    const todos = [matching, base]
    expect(selectTodos(todos, 'all', 'RELEASE', 'newest')).toEqual([matching])
  })

  it('sorts by due date and keeps undated tasks last', () => {
    const later: Todo = { ...base, id: 2, due_date: '2026-12-01' }
    const sooner: Todo = { ...base, id: 3, due_date: '2026-11-01' }
    const todos = [base, later, sooner]
    const ordered = selectTodos(todos, 'all', '', 'due')
    expect(ordered.map((todo) => todo.id)).toEqual([3, 2, 1])
  })

  it('breaks due date ties with the newest task first', () => {
    const older: Todo = { ...base, id: 4, due_date: '2026-11-01' }
    const newer: Todo = { ...base, id: 9, due_date: '2026-11-01' }
    expect(selectTodos([older, newer], 'all', '', 'due')).toEqual([
      newer,
      older,
    ])
  })

  it('sorts newest first by creation date and breaks ties by id', () => {
    const oldest: Todo = {
      ...base,
      id: 5,
      created_at: '2026-01-01T00:00:00Z',
    }
    const tieLower: Todo = {
      ...base,
      id: 2,
      created_at: '2026-05-01T00:00:00Z',
    }
    const tieHigher: Todo = {
      ...base,
      id: 8,
      created_at: '2026-05-01T00:00:00Z',
    }
    const ordered = selectTodos(
      [oldest, tieLower, tieHigher],
      'all',
      '',
      'newest',
    )
    expect(ordered.map((todo) => todo.id)).toEqual([8, 2, 5])
  })
})

describe('validateTodo', () => {
  it('returns no errors for a valid payload', () => {
    expect(validateTodo(validInput)).toEqual({})
  })

  it('rejects a missing or blank title', () => {
    expect(validateTodo({ ...validInput, title: '' })).toEqual({
      title: 'Enter a task title.',
    })
    expect(validateTodo({ ...validInput, title: '   ' })).toEqual({
      title: 'Enter a task title.',
    })
  })

  it('accepts a 120 character title and rejects 121 characters', () => {
    expect(validateTodo({ ...validInput, title: 'a'.repeat(120) })).toEqual({})
    expect(validateTodo({ ...validInput, title: 'a'.repeat(121) })).toEqual({
      title: 'The title must be at most 120 characters.',
    })
  })

  it('accepts a 2000 character description and rejects 2001', () => {
    expect(
      validateTodo({ ...validInput, description: 'a'.repeat(2000) }),
    ).toEqual({})
    expect(
      validateTodo({ ...validInput, description: 'a'.repeat(2001) }),
    ).toEqual({
      description: 'The description must be at most 2000 characters.',
    })
  })

  it('reports every invalid field at once', () => {
    expect(
      validateTodo({ ...validInput, title: ' ', due_date: '2026-02-30' }),
    ).toEqual({
      title: 'Enter a task title.',
      due_date: 'Enter a valid date.',
    })
  })

  it.each(malformedDates)('rejects the due date %s', (due_date) => {
    expect(validateTodo({ ...validInput, due_date })).toEqual({
      due_date: 'Enter a valid date.',
    })
  })

  it('accepts a real calendar date', () => {
    expect(validateTodo({ ...validInput, due_date: '2026-10-01' })).toEqual({})
  })
})

describe('isOverdue', () => {
  function freezeToday() {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-15T09:00:00'))
  }

  it('flags an unfinished task due yesterday', () => {
    freezeToday()
    try {
      expect(isOverdue({ ...base, due_date: '2026-10-14' })).toBe(true)
    } finally {
      vi.useRealTimers()
    }
  })

  it('does not flag a task due today', () => {
    freezeToday()
    try {
      expect(isOverdue({ ...base, due_date: '2026-10-15' })).toBe(false)
    } finally {
      vi.useRealTimers()
    }
  })

  it('does not flag a completed task or a task without a due date', () => {
    freezeToday()
    try {
      const completed: Todo = {
        ...base,
        due_date: '2026-10-14',
        completed: true,
      }
      expect(isOverdue(completed)).toBe(false)
      expect(isOverdue({ ...base, due_date: null })).toBe(false)
    } finally {
      vi.useRealTimers()
    }
  })
})

describe('formatDate', () => {
  it('formats a date as day, abbreviated month and year', () => {
    expect(formatDate('2026-10-01')).toBe('1 Oct 2026')
    expect(formatDate('2026-01-05')).toBe('5 Jan 2026')
  })
})
