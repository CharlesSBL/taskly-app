import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { request } from './http'

const fetchMock = vi.fn<(path: string, init?: RequestInit) => Promise<Response>>()

function response(status: number, body?: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response
}

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

it('calls the api prefix with JSON headers and resolves the parsed body', async () => {
  fetchMock.mockResolvedValue(response(200, { id: 7, title: 'Prepare a demo' }))

  await expect(request('/todos/7')).resolves.toEqual({
    id: 7,
    title: 'Prepare a demo',
  })

  expect(fetchMock).toHaveBeenCalledWith('/api/todos/7', {
    headers: { 'Content-Type': 'application/json' },
  })
})

it('keeps the caller method, body and extra headers while adding JSON headers', async () => {
  fetchMock.mockResolvedValue(response(201, { id: 8 }))

  await request('/todos', {
    method: 'POST',
    body: '{"title":"Prepare a demo"}',
    headers: { 'X-Trace-Id': 'abc' },
  })

  expect(fetchMock).toHaveBeenCalledWith('/api/todos', {
    method: 'POST',
    body: '{"title":"Prepare a demo"}',
    headers: { 'Content-Type': 'application/json', 'X-Trace-Id': 'abc' },
  })
})

it('resolves undefined for a 204 without parsing a body', async () => {
  const json = vi.fn()
  fetchMock.mockResolvedValue({
    ok: true,
    status: 204,
    json,
  } as unknown as Response)

  await expect(
    request('/todos/7', { method: 'DELETE' }),
  ).resolves.toBeUndefined()

  expect(json).not.toHaveBeenCalled()
})

it('reports a connection problem when the server is unreachable', async () => {
  fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

  await expect(request('/todos')).rejects.toThrow(
    'Cannot connect to the server. Please try again.',
  )
})

it('rethrows the original error when the caller aborted the request', async () => {
  const controller = new AbortController()
  controller.abort()
  const abortError = new DOMException('The operation was aborted.', 'AbortError')
  fetchMock.mockRejectedValue(abortError)

  await expect(
    request('/todos', { signal: controller.signal }),
  ).rejects.toBe(abortError)
})

it('uses the server detail message when the request is rejected', async () => {
  fetchMock.mockResolvedValue(response(404, { detail: 'Task not found.' }))

  await expect(request('/todos/99')).rejects.toThrow('Task not found.')
})

it('uses the validation message for a 422 even with a structured detail', async () => {
  fetchMock.mockResolvedValue(
    response(422, { detail: [{ loc: ['body', 'title'], msg: 'too long' }] }),
  )

  await expect(request('/todos', { method: 'POST' })).rejects.toThrow(
    'Check the task details: title up to 120 characters, description up to 2000 characters, and a valid due date.',
  )
})

it('falls back to a generic message when the detail is not a string', async () => {
  fetchMock.mockResolvedValue(response(500, { detail: { code: 'boom' } }))

  await expect(request('/todos')).rejects.toThrow(
    'The operation failed. Please try again.',
  )
})

it('falls back to a generic message when the error body is unreadable', async () => {
  fetchMock.mockResolvedValue({
    ok: false,
    status: 500,
    json: () => Promise.reject(new SyntaxError('Unexpected token')),
  } as unknown as Response)

  await expect(request('/todos')).rejects.toThrow(
    'The operation failed. Please try again.',
  )
})
