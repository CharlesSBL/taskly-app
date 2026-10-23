import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { useNotice } from './useNotice'

afterEach(() => {
  vi.useRealTimers()
})

it('starts without a notice and exposes a notification callback', () => {
  const { result } = renderHook(() => useNotice())
  expect(result.current.message).toBe('')
  expect(result.current.notify).toEqual(expect.any(Function))
})

it('shows the notified message immediately', () => {
  const { result } = renderHook(() => useNotice())

  act(() => result.current.notify('Task deleted.'))

  expect(result.current.message).toBe('Task deleted.')
})

it('clears the notice after four seconds', () => {
  vi.useFakeTimers()
  const { result } = renderHook(() => useNotice())
  act(() => result.current.notify('Task deleted.'))

  act(() => vi.advanceTimersByTime(3999))
  expect(result.current.message).toBe('Task deleted.')

  act(() => vi.advanceTimersByTime(1))
  expect(result.current.message).toBe('')
})

it('restarts the dismissal timer when a second notice arrives', () => {
  vi.useFakeTimers()
  const { result } = renderHook(() => useNotice())
  act(() => result.current.notify('First notice.'))
  act(() => vi.advanceTimersByTime(3000))

  act(() => result.current.notify('Second notice.'))
  act(() => vi.advanceTimersByTime(3000))

  expect(result.current.message).toBe('Second notice.')

  act(() => vi.advanceTimersByTime(1000))
  expect(result.current.message).toBe('')
})

it('cancels the pending dismissal timer when it unmounts', () => {
  vi.useFakeTimers()
  const clearTimeout = vi.spyOn(window, 'clearTimeout')
  const { result, unmount } = renderHook(() => useNotice())
  act(() => result.current.notify('Task deleted.'))

  unmount()

  expect(clearTimeout).toHaveBeenCalledTimes(1)
  clearTimeout.mockRestore()
})
