import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import type { Todo } from '../types'
import { TodoList } from './TodoList'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))
vi.mock('./TodoItem', () => ({
  TodoItem: vi.fn(
    ({
      todo,
      busy,
      onToggle,
      onEdit,
      onDelete,
    }: {
      todo: Todo
      busy: boolean
      onToggle: () => void
      onEdit: () => void
      onDelete: () => void
    }) => (
      <li>
        <span>{todo.title}</span>
        <span>{busy ? 'busy' : 'idle'}</span>
        <button type="button" onClick={onToggle}>
          Toggle {todo.title}
        </button>
        <button type="button" onClick={onEdit}>
          Edit {todo.title}
        </button>
        <button type="button" onClick={onDelete}>
          Delete {todo.title}
        </button>
      </li>
    ),
  ),
}))

type TodoListProps = Parameters<typeof TodoList>[0]

const otherTodo: Todo = { ...todoFixture, id: 3, title: 'Book the room' }

function listProps(overrides: Partial<TodoListProps> = {}) {
  return {
    todos: [],
    hasTodos: false,
    loading: false,
    failed: false,
    busy: false,
    onCreate: vi.fn(),
    onToggle: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
    ...overrides,
  } as TodoListProps
}

it('shows loading feedback before showing an empty list', () => {
  const props = listProps({ loading: true })
  const { rerender } = render(<TodoList {...props} />)
  expect(screen.getByRole('status')).toHaveTextContent('Loading your tasks…')
  expect(
    screen.queryByRole('heading', { name: 'Add your first task' }),
  ).not.toBeInTheDocument()

  rerender(<TodoList {...props} loading={false} />)

  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(
    screen.getByRole('heading', { name: 'Add your first task' }),
  ).toBeVisible()
})

it('offers to create the first task and forwards the request', async () => {
  const user = userEvent.setup()
  const onCreate = vi.fn()
  render(<TodoList {...listProps({ onCreate })} />)

  await user.click(screen.getByRole('button', { name: 'Add your first task' }))

  expect(onCreate).toHaveBeenCalledTimes(1)
})

it('disables the empty state action while the list is busy', () => {
  render(<TodoList {...listProps({ busy: true })} />)

  expect(
    screen.getByRole('button', { name: 'Add your first task' }),
  ).toBeDisabled()
})

it('explains a temporary outage when no task was ever loaded', () => {
  render(<TodoList {...listProps({ failed: true })} />)

  expect(
    screen.getByRole('heading', {
      name: 'The task list is temporarily unavailable',
    }),
  ).toBeVisible()
  expect(screen.getByText('Try again to load your tasks.')).toBeVisible()
  expect(
    screen.queryByRole('heading', { name: 'Add your first task' }),
  ).not.toBeInTheDocument()
})

it('keeps showing cached tasks when a refresh fails', () => {
  const props = listProps({
    failed: true,
    hasTodos: true,
    todos: [todoFixture],
  })
  render(<TodoList {...props} />)

  expect(screen.getByText(todoFixture.title)).toBeVisible()
  expect(
    screen.queryByRole('heading', {
      name: 'The task list is temporarily unavailable',
    }),
  ).not.toBeInTheDocument()
})

it('reports no match instead of offering to create a task', () => {
  render(<TodoList {...listProps({ hasTodos: true })} />)

  expect(
    screen.getByRole('heading', { name: 'No matching tasks' }),
  ).toBeVisible()
  expect(
    screen.queryByRole('button', { name: 'Add your first task' }),
  ).not.toBeInTheDocument()
})

it('renders every task and forwards its own handlers', async () => {
  const user = userEvent.setup()
  const onToggle = vi.fn()
  const onEdit = vi.fn()
  const onDelete = vi.fn()
  render(
    <TodoList
      {...listProps({
        todos: [todoFixture, otherTodo],
        onToggle,
        onEdit,
        onDelete,
      })}
    />,
  )

  const items = within(screen.getByRole('list')).getAllByRole('listitem')
  expect(items).toHaveLength(2)
  expect(screen.getByText(todoFixture.title)).toBeVisible()
  expect(screen.getByText(otherTodo.title)).toBeVisible()

  await user.click(
    screen.getByRole('button', { name: `Toggle ${todoFixture.title}` }),
  )
  await user.click(
    screen.getByRole('button', { name: `Edit ${otherTodo.title}` }),
  )
  await user.click(
    screen.getByRole('button', { name: `Delete ${otherTodo.title}` }),
  )

  expect(onToggle).toHaveBeenCalledWith(todoFixture)
  expect(onEdit).toHaveBeenCalledWith(otherTodo)
  expect(onDelete).toHaveBeenCalledWith(otherTodo)
})

it('passes the busy flag down to every task row', () => {
  const props = listProps({ todos: [todoFixture, otherTodo] })
  const { rerender } = render(<TodoList {...props} />)
  expect(screen.getAllByText('idle')).toHaveLength(2)

  rerender(<TodoList {...props} busy />)

  expect(screen.getAllByText('busy')).toHaveLength(2)
  expect(screen.queryAllByText('idle')).toHaveLength(0)
})
