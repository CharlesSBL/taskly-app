import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { todoFixture } from '../../test/todoFixture'
import { useTodoFilters } from './hooks/useTodoFilters'
import { useTodosBusy } from './hooks/useTodosBusy'
import { useTodosQuery } from './hooks/useTodosQuery'
import { useUpdateTodoMutation } from './hooks/useUpdateTodoMutation'
import { TodosPage } from './TodosPage'
import type { Todo } from './types'

vi.mock('../../design-system', () => import('../../design-system/mocks'))
vi.mock('./hooks/useTodoFilters', () => ({ useTodoFilters: vi.fn() }))
vi.mock('./hooks/useTodosBusy', () => ({ useTodosBusy: vi.fn() }))
vi.mock('./hooks/useTodosQuery', () => ({ useTodosQuery: vi.fn() }))
vi.mock('./hooks/useUpdateTodoMutation', () => ({
  useUpdateTodoMutation: vi.fn(),
}))
vi.mock('./components/TodosHeader', () => ({
  TodosHeader: ({ onCreate }: { onCreate: () => void }) => (
    <button type="button" onClick={onCreate}>
      New task
    </button>
  ),
}))
vi.mock('./components/TodoFilters', () => ({ TodoFilters: () => null }))
vi.mock('./components/TodoList', () => ({
  TodoList: ({
    todos,
    onToggle,
    onEdit,
    onDelete,
  }: {
    todos: Todo[]
    onToggle: (todo: Todo) => void
    onEdit: (todo: Todo) => void
    onDelete: (todo: Todo) => void
  }) => (
    <div>
      {todos.map((todo) => (
        <div key={todo.id}>
          <button type="button" onClick={() => onToggle(todo)}>
            Toggle
          </button>
          <button type="button" onClick={() => onEdit(todo)}>
            Edit
          </button>
          <button type="button" onClick={() => onDelete(todo)}>
            Delete
          </button>
        </div>
      ))}
    </div>
  ),
}))
vi.mock('./components/TodoEditor', () => ({
  TodoEditor: ({
    todo,
    onClose,
    onSaved,
  }: {
    todo: Todo | 'new'
    onClose: () => void
    onSaved: (message: string) => void
  }) => (
    <div role="dialog" aria-label="Editor">
      <p>{todo === 'new' ? 'Draft task' : todo.title}</p>
      <button type="button" onClick={onClose}>
        Close
      </button>
      <button type="button" onClick={() => onSaved('New task added.')}>
        Save
      </button>
    </div>
  ),
}))
vi.mock('./components/DeleteTodoDialog', () => ({
  DeleteTodoDialog: ({
    todo,
    onClose,
    onDeleted,
  }: {
    todo: Todo
    onClose: () => void
    onDeleted: () => void
  }) => (
    <div role="dialog" aria-label="Delete">
      <p>{todo.title}</p>
      <button type="button" onClick={onClose}>
        Cancel
      </button>
      <button type="button" onClick={onDeleted}>
        Confirm
      </button>
    </div>
  ),
}))

const mutateAsync = vi.fn()
const reset = vi.fn()
const refetch = vi.fn()

function stubPage({
  todos = [todoFixture],
  queryError = null,
  isFetching = false,
  busy = false,
}: {
  todos?: Todo[]
  queryError?: Error | null
  isFetching?: boolean
  busy?: boolean
} = {}) {
  vi.mocked(useTodosQuery).mockReturnValue({
    data: todos,
    isPending: false,
    isFetching,
    isError: queryError !== null,
    error: queryError,
    refetch,
  } as unknown as ReturnType<typeof useTodosQuery>)
  vi.mocked(useTodoFilters).mockReturnValue({
    filter: 'all',
    search: '',
    sort: 'newest',
    visible: todos,
    setFilter: vi.fn(),
    setSearch: vi.fn(),
    setSort: vi.fn(),
  })
  vi.mocked(useUpdateTodoMutation).mockReturnValue({
    error: null,
    reset,
    mutateAsync,
  } as unknown as ReturnType<typeof useUpdateTodoMutation>)
  vi.mocked(useTodosBusy).mockReturnValue(busy)
}

beforeEach(() => {
  vi.clearAllMocks()
  refetch.mockResolvedValue(undefined)
  reset.mockReturnValue(undefined)
})

it('displays a query failure and resets mutation errors before retrying', async () => {
  const user = userEvent.setup()
  stubPage({ queryError: new Error('The server is unavailable.') })
  render(<TodosPage />)

  expect(screen.getByTestId('alert')).toHaveTextContent(
    'The server is unavailable.',
  )

  await user.click(screen.getByRole('button', { name: 'Try again' }))

  await waitFor(() => expect(refetch).toHaveBeenCalledTimes(1))
  expect(reset).toHaveBeenCalledTimes(1)
  expect(reset.mock.invocationCallOrder[0]).toBeLessThan(
    refetch.mock.invocationCallOrder[0],
  )
})

it('notifies that a task is complete after a successful toggle', async () => {
  const user = userEvent.setup()
  const message = 'Another task complete. Well done!'
  stubPage()
  mutateAsync.mockResolvedValue({ ...todoFixture, completed: true })
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Toggle' }))

  await waitFor(() => {
    expect(screen.getByTestId('alert')).toHaveTextContent(message)
  })
  expect(mutateAsync).toHaveBeenCalledWith({
    id: 7,
    input: { completed: true },
  })
})

it('notifies that a task is active again when a done task is toggled', async () => {
  const user = userEvent.setup()
  const completed: Todo = { ...todoFixture, completed: true }
  stubPage({ todos: [completed] })
  mutateAsync.mockResolvedValue({ ...completed, completed: false })
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Toggle' }))

  await waitFor(() => {
    expect(screen.getByTestId('alert')).toHaveTextContent(
      'Task marked as active.',
    )
  })
  expect(mutateAsync).toHaveBeenCalledWith({
    id: 7,
    input: { completed: false },
  })
})

it('shows no notice when the toggle fails', async () => {
  const user = userEvent.setup()
  stubPage()
  mutateAsync.mockImplementation(() => Promise.reject(new Error('Offline.')))
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Toggle' }))

  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
  expect(screen.queryByTestId('alert')).not.toBeInTheDocument()
})

it('ignores a toggle while another task mutation is in flight', async () => {
  const user = userEvent.setup()
  stubPage({ busy: true })
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Toggle' }))

  expect(mutateAsync).not.toHaveBeenCalled()
})

it('disables the retry action while the task list is refetching', () => {
  stubPage({
    queryError: new Error('The server is unavailable.'),
    isFetching: true,
  })
  render(<TodosPage />)

  expect(screen.getByRole('button', { name: 'Try again' })).toBeDisabled()
})

it('opens a blank editor for a new task and shows the saved notice', async () => {
  const user = userEvent.setup()
  stubPage()
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'New task' }))
  const editor = screen.getByRole('dialog', { name: 'Editor' })
  expect(editor).toHaveTextContent('Draft task')

  await user.click(screen.getByRole('button', { name: 'Save' }))

  expect(screen.queryByRole('dialog', { name: 'Editor' })).toBeNull()
  expect(screen.getByTestId('alert')).toHaveTextContent('New task added.')
})

it('opens the editor for the task chosen in the list and closes it', async () => {
  const user = userEvent.setup()
  stubPage()
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Edit' }))
  const editor = screen.getByRole('dialog', { name: 'Editor' })
  expect(editor).toHaveTextContent('Prepare a demo')

  await user.click(screen.getByRole('button', { name: 'Close' }))

  expect(screen.queryByRole('dialog', { name: 'Editor' })).toBeNull()
})

it('notifies after the delete confirmation removes the chosen task', async () => {
  const user = userEvent.setup()
  stubPage()
  render(<TodosPage />)

  await user.click(screen.getByRole('button', { name: 'Delete' }))
  const confirmation = screen.getByRole('dialog', { name: 'Delete' })
  expect(confirmation).toHaveTextContent('Prepare a demo')

  await user.click(screen.getByRole('button', { name: 'Confirm' }))

  expect(screen.queryByRole('dialog', { name: 'Delete' })).toBeNull()
  expect(screen.getByTestId('alert')).toHaveTextContent('Task deleted.')
})
