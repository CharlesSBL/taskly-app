import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { TodosHeader } from './TodosHeader'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))

it('invokes creation when enabled and blocks it when disabled', async () => {
  const user = userEvent.setup()
  const onCreate = vi.fn()
  const { rerender } = render(
    <TodosHeader disabled={false} onCreate={onCreate} />,
  )
  expect(screen.getByRole('heading', { name: 'Tasks' })).toBeVisible()
  expect(
    screen.getByText('Create, organize, and complete tasks.'),
  ).toBeVisible()
  const button = screen.getByRole('button', { name: 'New task' })
  await user.click(button)
  expect(onCreate).toHaveBeenCalledTimes(1)
  rerender(<TodosHeader disabled onCreate={onCreate} />)
  expect(button).toBeDisabled()
  await user.click(button)
  expect(onCreate).toHaveBeenCalledTimes(1)
})

it('announces how many tasks are due soon', () => {
  const { rerender } = render(
    <TodosHeader disabled={false} dueSoonCount={2} onCreate={vi.fn()} />,
  )
  expect(screen.getByText('2 due soon')).toBeVisible()
  rerender(<TodosHeader disabled={false} dueSoonCount={5} onCreate={vi.fn()} />)
  expect(screen.getByText('5 due soon')).toBeVisible()
})

it('hides the due-soon badge when nothing is approaching', () => {
  const { rerender } = render(
    <TodosHeader disabled={false} dueSoonCount={0} onCreate={vi.fn()} />,
  )
  expect(screen.queryByText(/due soon/)).not.toBeInTheDocument()
  rerender(<TodosHeader disabled={false} onCreate={vi.fn()} />)
  expect(screen.queryByText(/due soon/)).not.toBeInTheDocument()
})
