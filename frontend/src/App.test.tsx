import { render, screen } from '@testing-library/react'
import { expect, it, vi } from 'vitest'
import App from './App'

vi.mock('./components/ApplicationHeader', () => ({
  ApplicationHeader: () => <header>Application header</header>,
}))
vi.mock('./features/todos', () => ({
  TodosPage: () => <main>Tasks page</main>,
}))

it('composes the application header and tasks page', () => {
  render(<App />)
  expect(screen.getByRole('banner')).toHaveTextContent('Application header')
  expect(screen.getByRole('main')).toHaveTextContent('Tasks page')
})
