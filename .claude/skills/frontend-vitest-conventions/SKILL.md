---
name: frontend-vitest-conventions
description: "Frontend test conventions for this repository, derived from colocated Vitest tests: RTL queries, design-system mocks, fixtures and mocking boundaries."
---

# Frontend Vitest conventions

Derived from the files below. Follow them; do not invent a second style.

- `frontend/vite.config.ts` — jsdom, `src/test/setup.ts`, coverage excludes
- `frontend/src/design-system/mocks.tsx` — the mocked design system
- `frontend/src/test/todoFixture.ts` — shared `Todo` fixture
- `frontend/src/App.test.tsx`, `components/ApplicationHeader.test.tsx`,
  `components/SuccessNotice.test.tsx`, `hooks/useNotice.test.ts`
- `frontend/src/features/todos/TodosPage.test.tsx`,
  `components/DeleteTodoDialog.test.tsx`, `api/todos.test.ts`

## Layout and setup

- Tests are colocated: `Foo.tsx` → `Foo.test.tsx` (or `.test.ts`).
- Import the API from `vitest` explicitly: `import { expect, it, vi } from 'vitest'`.
  The repo does not enable globals.
- `src/test/setup.ts` adds jest-dom and calls `cleanup` after each test; do not
  repeat either.
- Formatting is Prettier with `semi: false`, `singleQuote: true`,
  `trailingComma: "all"`.

## Mocking boundaries

- Design system: always
  `vi.mock('../../design-system', () => import('../../design-system/mocks'))`
  (adjust the relative depth). The real components are excluded from coverage.
- HTTP: mock `lib/http`, not `fetch`:
  `vi.mock('../../../lib/http', () => ({ request: vi.fn() }))` and
  `vi.mocked(request).mockResolvedValue(todoFixture)`.
- Hooks: mock the hook module and return a typed value, e.g.
  `vi.mocked(useTodosQuery).mockReturnValue({ ... } as unknown as ReturnType<typeof useTodosQuery>)`.
- Mock only module boundaries. Never mock the component or function under test.
- Call `beforeEach(() => vi.clearAllMocks())` when a test asserts on mock calls.

## Queries and interactions

- Query by role and accessible name first: `screen.getByRole('button', { name: 'Cancel' })`,
  `within(header).getByRole('link', { name: 'Taskly — home' })`.
- `getByTestId` is only acceptable for the design-system mocks (for example
  `screen.getByTestId('alert')`), because those components are intentionally dumb.
- Use `userEvent.setup()` and `await user.click(...)`; never `fireEvent` for
  clicks when user-event is available.
- Use `waitFor` only for genuinely async UI (`await waitFor(() => expect(refetch).toHaveBeenCalled())`).
- Assert rendered text and attributes, not implementation details:
  `expect(link).toHaveAttribute('href', '/')`.
- When asserting props passed to a mocked design-system component, inspect
  `vi.mocked(Alert).mock.calls[0][0]` with `expect.objectContaining`.

## Hooks and API modules

- Hook tests use `renderHook(() => useNotice())` and assert returned values.
- API tests assert the exact request:
  `expect(request).toHaveBeenCalledWith('/todos', { signal })`.
- For components that receive data, use `todoFixture` instead of building a new
  object, unless the test needs different values.

## Determinism

- No real timers, network or randomness. Use `vi.useFakeTimers()` and restore it
  in the same test when timing matters.
- Do not snapshot. Assert specific text, roles and values.
- Remember that `TodosPage` tests mock the whole todos feature surface; a test
  should drive only the behavior it names.

## Verify and format

Before finishing:

```
run_vitest({"paths": ["frontend/src/features/todos/components/Foo.test.tsx"]})
run_lint({"stack": "frontend"})
```

The gate runs `tsc --noEmit` and `prettier --check` on the generated files with
the repository config in `frontend/.prettierrc.json`: no semicolons, single
quotes and trailing commas. Match the existing test files exactly; a formatting
difference reverts the stack.

`tsc --noEmit` and `prettier --check` run in the gate; keep tests type-clean and
formatted.
