import { expect, it } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import type { Todo } from '../types'
import { isDueSoon } from './due'

const TODAY = new Date(2026, 9, 1)

function todoDue(dueDate: string | null, overrides: Partial<Todo> = {}): Todo {
  return { ...todoFixture, due_date: dueDate, ...overrides }
}

it.each([
  [true, 'today', '2026-10-01'],
  [true, 'the last day of the window', '2026-10-04'],
  [false, 'the day after the window', '2026-10-05'],
  [false, 'yesterday', '2026-09-30'],
])('returns %s when the task is due %s', (expected, _label, dueDate) => {
  expect(isDueSoon(todoDue(dueDate), TODAY)).toBe(expected)
})

it('ignores tasks without a due date', () => {
  expect(isDueSoon(todoDue(null), TODAY)).toBe(false)
})

it('ignores completed tasks even when they are due today', () => {
  expect(isDueSoon(todoDue('2026-10-01', { completed: true }), TODAY)).toBe(false)
})

it('widens the window with the days argument', () => {
  expect(isDueSoon(todoDue('2026-10-06'), TODAY, 5)).toBe(true)
  expect(isDueSoon(todoDue('2026-10-07'), TODAY, 5)).toBe(false)
})
