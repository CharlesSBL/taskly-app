import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import { TodoFilters } from './TodoFilters'

vi.mock('../../../design-system', () => import('../../../design-system/mocks'))

it('displays controlled values and forwards all filter changes', async () => {
  const user = userEvent.setup()
  const callbacks = {
    onFilterChange: vi.fn(),
    onSearchChange: vi.fn(),
    onSortChange: vi.fn(),
  }
  const { rerender } = render(
    <TodoFilters filter="all" search="" sort="newest" {...callbacks} />,
  )
  await user.type(screen.getByLabelText('Search tasks'), 'a')
  await user.selectOptions(screen.getByLabelText('Status'), 'completed')
  await user.selectOptions(screen.getByLabelText('Sort by'), 'due')
  expect(callbacks.onSearchChange).toHaveBeenCalledWith('a')
  expect(callbacks.onFilterChange).toHaveBeenCalledWith('completed')
  expect(callbacks.onSortChange).toHaveBeenCalledWith('due')
  rerender(
    <TodoFilters filter="completed" search="demo" sort="due" {...callbacks} />,
  )
  expect(screen.getByLabelText('Search tasks')).toHaveValue('demo')
  expect(screen.getByLabelText('Status')).toHaveValue('completed')
  expect(screen.getByLabelText('Sort by')).toHaveValue('due')
})
