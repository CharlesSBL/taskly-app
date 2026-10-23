---
name: test-quality-review
description: "Self-check generated tests before finishing: real assertions, regression sensitivity, determinism, branches and error paths."
---

# Review test quality before you finish

Run this checklist against every file you are about to submit. If a test fails
the review, fix it or drop the claim; do not submit it.

## Would it fail if the code broke?

- Each test must assert an observable result (return value, response body,
  rendered text, repository call, raised error).
- Mentally mutate the implementation: flip a condition, change an operator,
  remove the error branch. At least one test must fail.
- Reject tests that only prove "the function was called" when the return value
  or output is the behavior under test.

## Real assertions

- No `assert True`, `assert 1`, `expect(true).toBe(true)` or assertion-free
  tests.
- Do not assert on mocks you configured yourself unless the call itself is the
  contract (for example the repository receives a `TodoCreate` payload).
- Python: use `pytest.raises(..., match=...)` for errors and assert the message.
- TypeScript: assert DOM text, roles, attributes, or the resolved value; use
  `toHaveBeenCalledWith` only for genuine boundary calls.

## Determinism

- No `sleep`, real network, real database, real clock or unseeded randomness.
- Python: freeze or inject time; use `monkeypatch` for environment variables.
- TypeScript: use `vi.useFakeTimers()` only when testing timers and restore it;
  `await waitFor(...)` only for asynchronous UI.
- No ordering assumptions that depend on dict or filesystem order.

## Coverage of behavior

For each changed function, consider:

1. happy path with representative input,
2. validation and boundary values (empty, max length, wrong type),
3. error and not-found paths,
4. empty collections and the default branch.

Do not duplicate a test that already exists; extend it instead.

## Repository fit

- Reuse `backend/tests/conftest.py` fixtures (`client`, `repository_mock`,
  `todo`, `model_factory`) and `frontend/src/test/todoFixture.ts`.
- Mock at the existing boundaries: `create_autospec(TodoRepository)` and
  `Mock(spec=Session)` on the backend; `vi.mock` of `lib/http`, hooks or
  `design-system/mocks` on the frontend.
- Never mock the unit under test.
- Do not modify `conftest.py`, fixtures or application source.

## Verification

- Run the new tests with `run_pytest` / `run_vitest` before `finish`.
- A failure caused by the test is your bug: fix the test. A failure caused by
  pre-existing application code means the baseline is broken; report it instead
  of changing source.
- Only claim a behavior in `test_claims` if a passing test asserts it.
