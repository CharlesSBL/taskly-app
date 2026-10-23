---
name: backend-pytest-conventions
description: "Backend test conventions for this repository, derived from backend/tests: fixtures, mocking boundaries, pytest style and coverage."
---

# Backend pytest conventions

Derived from the files below. Follow them; do not invent a second style.

- `backend/tests/conftest.py` — shared fixtures
- `backend/tests/mocks.py` — `make_repository_mock()`
- `backend/tests/features/todos/test_repository.py`, `test_router.py`,
  `test_validators.py`
- `backend/tests/api/test_dependencies.py`, `backend/tests/core/test_database.py`
- `backend/pyproject.toml` — pytest and coverage configuration

## Layout

- Tests mirror the application: `app/features/todos/repository.py` is tested by
  `tests/features/todos/test_repository.py`.
- Every directory under `backend/tests/` has an `__init__.py`. When you add a
  new test directory, write an **empty** `backend/tests/<path>/__init__.py`.
- Run pytest with `cwd=backend`; that is where `pyproject.toml` and its coverage
  omits are read. The sandbox already does this.

## Fixtures you should reuse

| Fixture           | What it gives you                                                        |
| ----------------- | ------------------------------------------------------------------------ |
| `client`          | `TestClient` with only the todos router mounted and `get_repository` overridden |
| `repository_mock` | `create_autospec(TodoRepository, instance=True)`, `list()` returns `[]`   |
| `todo_values`     | A complete dict of `Todo` fields, including `priority` and timestamps     |
| `todo`            | `Todo.model_validate(todo_values)`                                        |
| `model_factory`   | `lambda values: TodoRecord(**values)` for repository tests                |

Do not edit `conftest.py` or `mocks.py`. If you need a local fixture, define it
in the test module.

## Style

- Absolute imports: `from app.features.todos.repository import TodoRepository`.
- One behavior per test, Arrange–Act–Assert, no comments narrating the code.
- Names state the behavior: `test_rejects_an_empty_patch`,
  `test_get_returns_none_for_missing_task`.
- `pytest.mark.parametrize` for input matrices (see `test_router.py` and
  `test_validators.py`).
- Assert both the result and the interaction:
  `repository_mock.create.assert_called_once_with(TodoCreate(...))`.

## Mocking boundaries

- Database/session: `Mock(spec=Session)`; inspect the statement with
  `session.scalars.call_args.args[0]`, `statement.compare(expected)` and the
  compiled PostgreSQL SQL (see `test_repository.py`).
- Repository: `create_autospec(TodoRepository, instance=True)`; never mock the
  unit under test.
- Never open a network connection or a real database. `TestClient` runs the
  ASGI app in-process.
- For a failing dependency, use `Mock(side_effect=...)` and assert the error
  propagates (see `test_dependencies.py`).

## Error and boundary coverage

- Validation: `pytest.raises(ValidationError, match="...")` for schemas and
  validators; `TestClient` returns 422 without calling the repository.
- Router: assert 404 branches, status codes (201, 204) and
  `response.json() == todo.model_dump(mode="json")`.
- Repository: missing rows return `None`, deletes return `False`, patches use
  `model_dump(exclude_unset=True)`.

## Environment

`core/config.py` tests must set `POSTGRES_*` or `DATABASE_URL` with
`monkeypatch.setenv` (or delete them with `monkeypatch.delenv`) because the
sandbox runs with `env -i`. Never depend on the ambient environment.

## Verify

Run the new tests through the sandbox tool before finishing:

```
run_pytest({"paths": ["backend/tests/features/todos/test_repository.py"]})
```
