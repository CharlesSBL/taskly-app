import type { Filter, Sort, Todo, TodoInput } from '../types'

export const priorityLabels = { low: 'Low', medium: 'Medium', high: 'High' }
const priorityOrder = { high: 0, medium: 1, low: 2 }

export function validateTodo(input: TodoInput): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!input.title.trim()) errors.title = 'Enter a task title.'
  else if (input.title.trim().length > 120)
    errors.title = 'The title must be at most 120 characters.'
  if (input.description.trim().length > 2000)
    errors.description = 'The description must be at most 2000 characters.'
  if (input.due_date) {
    const date = new Date(`${input.due_date}T00:00:00Z`)
    if (
      !/^\d{4}-\d{2}-\d{2}$/.test(input.due_date) ||
      Number.isNaN(date.getTime()) ||
      date.toISOString().slice(0, 10) !== input.due_date
    ) {
      errors.due_date = 'Enter a valid date.'
    }
  }
  return errors
}

export function selectTodos(
  todos: Todo[],
  filter: Filter,
  query: string,
  sort: Sort,
): Todo[] {
  const search = query.trim().toLocaleLowerCase('en')
  return todos
    .filter((todo) => {
      const statusMatches =
        filter === 'all' ||
        (filter === 'completed' ? todo.completed : !todo.completed)
      return (
        statusMatches &&
        `${todo.title} ${todo.description}`
          .toLocaleLowerCase('en')
          .includes(search)
      )
    })
    .sort((a, b) => {
      if (sort === 'priority')
        return (
          priorityOrder[a.priority] - priorityOrder[b.priority] || b.id - a.id
        )
      if (sort === 'due')
        return (
          (a.due_date ?? '9999').localeCompare(b.due_date ?? '9999') ||
          b.id - a.id
        )
      return b.created_at.localeCompare(a.created_at) || b.id - a.id
    })
}

export function isOverdue(todo: Todo): boolean {
  const today = new Date()
  const localDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  return !todo.completed && !!todo.due_date && todo.due_date < localDate
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${date}T12:00:00`))
}
