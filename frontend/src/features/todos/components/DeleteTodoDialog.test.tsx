import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi, type Mock } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { useDeleteTodoMutation } from '../hooks/useDeleteTodoMutation'
import { DeleteTodoDialog } from './DeleteTodoDialog'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))
vi.mock('../hooks/useDeleteTodoMutation', () => ({
  useDeleteTodoMutation: vi.fn(),
}))

type MutationStub = {
  isPending?: boolean
  error?: Error | null
  mutateAsync?: Mock
}

function mockDelete({ isPending, error, mutateAsync }: MutationStub) {
  const remove = mutateAsync ?? vi.fn()
  vi.mocked(useDeleteTodoMutation).mockReturnValue({
    isPending: isPending ?? false,
    error: error ?? null,
    mutateAsync: remove,
  } as unknown as ReturnType<typeof useDeleteTodoMutation>)
  return remove
}

function renderDialog(busy = false) {
  const onClose = vi.fn()
  const onDeleted = vi.fn()
  render(
    <DeleteTodoDialog
      todo={todoFixture}
      busy={busy}
      onClose={onClose}
      onDeleted={onDeleted}
    />,
  )
  return { onClose, onDeleted }
}

beforeEach(() => vi.clearAllMocks())

it('shows a deletion error and allows cancelling without deleting', async () => {
  const user = userEvent.setup()
  const remove = mockDelete({ error: new Error('Could not delete.') })
  const { onClose, onDeleted } = renderDialog()

  expect(screen.getByRole('dialog', { name: 'Delete task?' })).toBeVisible()
  expect(
    screen.getByText(
      `The task “${todoFixture.title}” will be permanently deleted.`,
    ),
  ).toBeVisible()
  expect(screen.getByTestId('alert')).toHaveTextContent('Could not delete.')

  await user.click(screen.getByRole('button', { name: 'Cancel' }))

  expect(onClose).toHaveBeenCalledTimes(1)
  expect(remove).not.toHaveBeenCalled()
  expect(onDeleted).not.toHaveBeenCalled()
})

it('deletes the task and reports the deletion once it succeeds', async () => {
  const user = userEvent.setup()
  const remove = mockDelete({
    mutateAsync: vi.fn().mockResolvedValue(undefined),
  })
  const { onClose, onDeleted } = renderDialog()

  await user.click(screen.getByRole('button', { name: 'Delete task' }))

  expect(remove).toHaveBeenCalledWith(todoFixture.id)
  await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1))
  expect(onClose).not.toHaveBeenCalled()
  expect(screen.queryByTestId('alert')).not.toBeInTheDocument()
})

it('keeps the confirmation open when the server rejects the deletion', async () => {
  const user = userEvent.setup()
  const remove = mockDelete({
    error: new Error('Task not found.'),
    mutateAsync: vi.fn().mockRejectedValue(new Error('Task not found.')),
  })
  const { onDeleted } = renderDialog()

  await user.click(screen.getByRole('button', { name: 'Delete task' }))

  await waitFor(() => expect(remove).toHaveBeenCalledTimes(1))
  expect(onDeleted).not.toHaveBeenCalled()
  expect(screen.getByRole('dialog', { name: 'Delete task?' })).toBeVisible()
  expect(screen.getByTestId('alert')).toHaveTextContent('Task not found.')
})

it('locks both actions while the page reports a running mutation', async () => {
  const user = userEvent.setup()
  const remove = mockDelete({})
  renderDialog(true)

  const confirm = screen.getByRole('button', { name: 'Deleting…' })
  expect(confirm).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()

  await user.click(confirm)

  expect(remove).not.toHaveBeenCalled()
})

it('shows the pending label while its own mutation is running', () => {
  mockDelete({ isPending: true })
  renderDialog()

  expect(screen.getByRole('button', { name: 'Deleting…' })).toBeDisabled()
  expect(screen.queryByTestId('alert')).not.toBeInTheDocument()
})
