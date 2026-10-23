import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { useNotice } from '../../hooks/useNotice'
import { todoFixture } from '../../test/todoFixture'
import { useTodoFilters } from './hooks/useTodoFilters'
import { useTodosBusy } from './hooks/useTodosBusy'
import { useTodosQuery } from './hooks/useTodosQuery'
import { useUpdateTodoMutation } from './hooks/useUpdateTodoMutation'
import { TodosPage } from './TodosPage'
import type { Todo } from './types'

vi.mock('../../design-system', () => import('../../design-system/mocks'))
vi.mock('../../hooks/useNotice', () => ({ useNotice: vi.fn() }))
vi.mock('./hooks/useTodoFilters', () => ({ useTodoFilters: vi.fn() }))
vi.mock('./hooks/useTodosBusy', () => ({ useTodosBusy: vi.fn() }))
vi.mock('./hooks/useTodosQuery', () => ({ useTodosQuery: vi.fn() }))
vi.mock('./hooks/useUpdateTodoMutation', () => ({
  useUpdateTodoMutation: vi.fn(),
}))
vi.mock('./components/TodosHeader', () => ({
  TodosHeader: () => <h1>Tasks</h1>,
}))
vi.mock('./components/TodoFilters', () => ({ TodoFilters: () => null }))
vi.mock('./components/TodoList', () => ({
  TodoList: ({
    todos,
    onToggle,
  }: {
    todos: Todo[]
    onToggle: (todo: Todo) => void
  }) => (
    <ul>
      {todos.map((todo) => (
        <li key={todo.id}>
          <button type="button" onClick={() => onToggle(todo)}>
            Toggle {todo.title}
          </button>
        </li>
      ))}
    </ul>
  ),
}))
vi.mock('./components/TodoEditor', () => ({ TodoEditor: () => null }))
vi.mock('./components/DeleteTodoDialog', () => ({
  DeleteTodoDialog: () => null,
}))
vi.mock('../../components/SuccessNotice', () => ({
  SuccessNotice: () => null,
}))

type QueryState = ReturnType<typeof useTodosQuery>
type MutationState = ReturnType<typeof useUpdateTodoMutation>

function renderTodosPage({
  query = {},
  mutation = {},
  busy = false,
  notify = vi.fn(),
  visible = [todoFixture],
}: {
  query?: Partial<QueryState>
  mutation?: Partial<MutationState>
  busy?: boolean
  notify?: (message: string) => void
  visible?: Todo[]
} = {}) {
  vi.mocked(useTodosQuery).mockReturnValue({
    data: visible,
    isPending: false,
    isFetching: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
    ...query,
  } as unknown as QueryState)
  vi.mocked(useUpdateTodoMutation).mockReturnValue({
    error: null,
    reset: vi.fn(),
    mutateAsync: vi.fn(),
    ...mutation,
  } as unknown as MutationState)
  vi.mocked(useTodosBusy).mockReturnValue(busy)
  vi.mocked(useNotice).mockReturnValue({ message: '', notify })
  vi.mocked(useTodoFilters).mockReturnValue({
    filter: 'all',
    search: '',
    sort: 'newest',
    visible,
    setFilter: vi.fn(),
    setSearch: vi.fn(),
    setSort: vi.fn(),
  })
  render(<TodosPage />)
}

const toggleButton = () =>
  screen.getByRole('button', { name: `Toggle ${todoFixture.title}` })

beforeEach(() => {
  vi.clearAllMocks()
})

it('displays a query failure and resets mutation errors before retrying', async () => {
  const user = userEvent.setup()
  const refetch = vi.fn().mockResolvedValue(undefined)
  const reset = vi.fn()
  vi.mocked(useTodosQuery).mockReturnValue({
    data: [],
    isPending: false,
    isFetching: false,
    isError: true,
    error: new Error('The server is unavailable.'),
    refetch,
  } as unknown as ReturnType<typeof useTodosQuery>)
  vi.mocked(useUpdateTodoMutation).mockReturnValue({
    error: null,
    reset,
    mutateAsync: vi.fn(),
  } as unknown as ReturnType<typeof useUpdateTodoMutation>)
  vi.mocked(useTodosBusy).mockReturnValue(false)
  vi.mocked(useNotice).mockReturnValue({ message: '', notify: vi.fn() })
  vi.mocked(useTodoFilters).mockReturnValue({
    filter: 'all',
    search: '',
    sort: 'newest',
    visible: [],
    setFilter: vi.fn(),
    setSearch: vi.fn(),
    setSort: vi.fn(),
  })
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

it('completes the task and announces it', async () => {
  const user = userEvent.setup()
  const notify = vi.fn()
  const mutateAsync = vi
    .fn()
    .mockResolvedValue({ ...todoFixture, completed: true })
  renderTodosPage({ mutation: { mutateAsync }, notify })

  await user.click(toggleButton())

  expect(mutateAsync).toHaveBeenCalledWith({
    id: todoFixture.id,
    input: { completed: true },
  })
  await waitFor(() =>
    expect(notify).toHaveBeenCalledWith('Another task complete. Well done!'),
  )
})

it('reopens a completed task and announces it', async () => {
  const user = userEvent.setup()
  const notify = vi.fn()
  const mutateAsync = vi
    .fn()
    .mockResolvedValue({ ...todoFixture, completed: false })
  renderTodosPage({
    mutation: { mutateAsync },
    notify,
    visible: [{ ...todoFixture, completed: true }],
  })

  await user.click(toggleButton())

  expect(mutateAsync).toHaveBeenCalledWith({
    id: todoFixture.id,
    input: { completed: false },
  })
  await waitFor(() =>
    expect(notify).toHaveBeenCalledWith('Task marked as active.'),
  )
})

it('ignores toggles while the page is busy', async () => {
  const user = userEvent.setup()
  const mutateAsync = vi.fn()
  renderTodosPage({ mutation: { mutateAsync }, busy: true })

  await user.click(toggleButton())

  expect(mutateAsync).not.toHaveBeenCalled()
})

it('stays silent when the toggle request fails', async () => {
  const user = userEvent.setup()
  const notify = vi.fn()
  const mutateAsync = vi.fn().mockRejectedValue(new Error('Request failed'))
  renderTodosPage({ mutation: { mutateAsync }, notify })

  await user.click(toggleButton())

  await waitFor(() => expect(mutateAsync).toHaveBeenCalledTimes(1))
  expect(notify).not.toHaveBeenCalled()
})
