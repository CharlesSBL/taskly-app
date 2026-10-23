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

it('shows the notified message', () => {
  const { result } = renderHook(() => useNotice())

  act(() => result.current.notify('Task saved.'))

  expect(result.current.message).toBe('Task saved.')
})

it('replaces the visible message when notify is called again', () => {
  vi.useFakeTimers()
  const { result } = renderHook(() => useNotice())

  act(() => result.current.notify('Task saved.'))
  act(() => result.current.notify('Task deleted.'))

  expect(result.current.message).toBe('Task deleted.')
})

it('clears the message after four seconds', () => {
  vi.useFakeTimers()
  const { result } = renderHook(() => useNotice())

  act(() => result.current.notify('Task saved.'))
  act(() => {
    vi.advanceTimersByTime(3999)
  })
  expect(result.current.message).toBe('Task saved.')

  act(() => {
    vi.advanceTimersByTime(1)
  })
  expect(result.current.message).toBe('')
})

it('cancels the pending timer when it unmounts', () => {
  vi.useFakeTimers()
  const clearTimeout = vi.spyOn(window, 'clearTimeout')
  const { result, unmount } = renderHook(() => useNotice())

  act(() => result.current.notify('Task saved.'))
  unmount()

  expect(clearTimeout).toHaveBeenCalled()
})
