import { render, screen } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { Alert } from '../design-system'
import { SuccessNotice } from './SuccessNotice'

vi.mock('../design-system', () => import('../design-system/mocks'))
beforeEach(() => vi.clearAllMocks())

it('renders nothing without a message', () => {
  const { container } = render(<SuccessNotice message="" />)
  expect(container).toBeEmptyDOMElement()
  expect(Alert).not.toHaveBeenCalled()
})

it('passes success messages to Alert and removes the notice when cleared', () => {
  const { container, rerender } = render(
    <SuccessNotice message="Task created." />,
  )
  expect(screen.getByTestId('alert')).toHaveTextContent('Task created.')
  expect(vi.mocked(Alert).mock.calls[0][0]).toEqual(
    expect.objectContaining({ variant: 'success' }),
  )
  rerender(<SuccessNotice message="Task deleted." />)
  expect(screen.getAllByTestId('alert')).toHaveLength(1)
  expect(screen.getByTestId('alert')).toHaveTextContent('Task deleted.')
  expect(screen.queryByText('Task created.')).not.toBeInTheDocument()
  rerender(<SuccessNotice message="" />)
  expect(container).toBeEmptyDOMElement()
})
