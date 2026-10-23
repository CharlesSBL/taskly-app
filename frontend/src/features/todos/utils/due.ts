import type { Todo } from '../types'

/**
 * True when the task is not completed and is due between today and
 * today + `days` (inclusive). Dates are compared in local time.
 */
export function isDueSoon(todo: Todo, today = new Date(), days = 3): boolean {
  if (!todo.due_date || todo.completed) return false
  const start = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  )
  const due = new Date(`${todo.due_date}T00:00:00`)
  const limit = new Date(start)
  limit.setDate(limit.getDate() + days)
  return due >= start && due <= limit
}
