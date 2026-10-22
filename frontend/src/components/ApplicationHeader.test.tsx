import { render, screen, within } from '@testing-library/react'
import { beforeEach, expect, it, vi } from 'vitest'
import { Heading, Text } from '../design-system'
import { ApplicationHeader } from './ApplicationHeader'

vi.mock('../design-system', () => import('../design-system/mocks'))
beforeEach(() => vi.clearAllMocks())

it('provides a home link, application title and task list description', () => {
  render(<ApplicationHeader />)
  const header = screen.getByRole('banner')
  const link = within(header).getByRole('link', { name: 'Taskly — home' })
  expect(link).toHaveAttribute('href', '/')
  expect(link).toHaveTextContent('Taskly')
  expect(vi.mocked(Heading).mock.calls[0][0]).toEqual(
    expect.objectContaining({ level: 2, children: 'Taskly' }),
  )
  expect(within(header).getByText('Task list')).toBeVisible()
  expect(vi.mocked(Text).mock.calls[0][0]).toEqual(
    expect.objectContaining({ muted: true, children: 'Task list' }),
  )
})
