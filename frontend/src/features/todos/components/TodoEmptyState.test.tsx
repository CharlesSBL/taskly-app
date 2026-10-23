import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { TodoEmptyState } from './TodoEmptyState'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))

beforeEach(() => vi.clearAllMocks())

it('invites the user to add a first task and reports the click', async () => {
  const user = userEvent.setup()
  const onCreate = vi.fn()
  render(
    <TodoEmptyState hasTodos={false} disabled={false} onCreate={onCreate} />,
  )

  expect(
    screen.getByRole('heading', { level: 3, name: 'Add your first task' }),
  ).toBeVisible()
  expect(
    screen.getByText('Write down what you need to do and get started.'),
  ).toBeVisible()

  await user.click(screen.getByRole('button', { name: 'Add your first task' }))

  expect(onCreate).toHaveBeenCalledOnce()
})

it('disables the add button while a task is being created', async () => {
  const user = userEvent.setup()
  const onCreate = vi.fn()
  render(<TodoEmptyState hasTodos={false} disabled onCreate={onCreate} />)

  const button = screen.getByRole('button', { name: 'Add your first task' })
  expect(button).toBeDisabled()

  await user.click(button)

  expect(onCreate).not.toHaveBeenCalled()
})

it('explains an empty filter instead of offering a create button', () => {
  const onCreate = vi.fn()
  render(<TodoEmptyState hasTodos disabled={false} onCreate={onCreate} />)

  expect(
    screen.getByRole('heading', { level: 3, name: 'No matching tasks' }),
  ).toBeVisible()
  expect(
    screen.getByText('Change the status filter or search to find your tasks.'),
  ).toBeVisible()
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
  expect(onCreate).not.toHaveBeenCalled()
})
