# Coverage baseline

Measured on a clean clone of commit `b003277` (the imported application), with
the application's own dependency files. These numbers are the reference the
agent's coverage delta is computed against.

| Stack    | Test files | Tests | Coverage                                       |
| -------- | ---------: | ----: | ---------------------------------------------- |
| Backend  |          6 |    21 | 42% (statement + branch, coverage.py)          |
| Frontend |         14 |    18 | 46.42% statements / 47.68% lines (v8)          |

Environment: Python 3.12.3, Node 24.22.1, `pytest-cov` 7.1.0,
`@vitest/coverage-v8` 4.1.11.

## How to reproduce

```sh
# backend
python3 -m venv .venv
.venv/bin/pip install --only-binary=:all: -r backend/requirements.txt
cd backend && ../.venv/bin/python -m pytest --cov=app --cov-report=term-missing

# frontend
cd frontend && npm ci --ignore-scripts && npx vitest run --coverage
```

Coverage is only correct when the backend suite runs with `cwd=backend`: that
is where `backend/pyproject.toml` is picked up (`branch=true`, and the omits for
`models`, `schemas`, `main` and package `__init__` files).

## Backend, per module

| Module                                | Stmts | Miss | Branch | Cover | Uncovered        |
| ------------------------------------- | ----: | ---: | -----: | ----: | ---------------- |
| `app/api/dependencies.py`             |    13 |    6 |      0 |   54% | 11-17            |
| `app/api/health.py`                   |     9 |    9 |      0 |    0% | 1-13             |
| `app/core/config.py`                  |    10 |   10 |      2 |    0% | 1-13             |
| `app/core/database.py`                |     9 |    2 |      0 |   78% | 16, 20           |
| `app/core/lifespan.py`                |    11 |   11 |      0 |    0% | 1-16             |
| `app/factory.py`                      |    11 |   11 |      0 |    0% | 1-14             |
| `app/features/todos/mappers.py`       |     4 |    0 |      0 |  100% | -                |
| `app/features/todos/repository.py`    |    39 |   21 |      6 |   40% | 24-29, 32-40, 43-48 |
| `app/features/todos/router.py`        |    29 |   11 |      6 |   51% | 24-27, 32-35, 40-42 |
| `app/features/todos/validators.py`    |    10 |    0 |      6 |  100% | -                |
| **Total**                             |   145 |   81 |     20 |   42% |                  |

`backend/tests/conftest.py` mounts only the todos router, so the application
factory, lifespan, configuration and health endpoint are untested. The
repository tests cover only the read path; create/update/delete and the
not-found branches are uncovered.

## Frontend, per area

| Area                            | Stmts | Branch | Funcs | Lines | Notes                          |
| ------------------------------- | ----: | -----: | ----: | ----: | ------------------------------ |
| `src/app/AppProviders.tsx`      |     0 |      0 |     0 |     0 | no test                        |
| `src/features/todos/TodosPage.tsx` | 48.14 | 61.11 | 27.27 |    50 | hooks mocked away            |
| `src/features/todos/api/todos.ts` | 57.14 | 100 | 50 | 57.14 | error paths uncovered         |
| `src/features/todos/components/DeleteTodoDialog.tsx` | 33.33 | 62.5 | 33.33 | 37.5 | confirm/cancel uncovered |
| `src/features/todos/components/TodoEditor.tsx` | 83.33 | 62.5 | 100 | 90 | one branch uncovered     |
| `src/features/todos/components/TodoEmptyState.tsx` | 0 | 0 | 0 | 0 | no test                    |
| `src/features/todos/components/TodoForm.tsx` | 88.23 | 63.63 | 77.77 | 87.5 | two branches uncovered   |
| `src/features/todos/components/TodoItem.tsx` | 100 | 35.71 | 100 | 100 | branches untested        |
| `src/features/todos/components/TodoList.tsx` | 20 | 62.5 | 20 | 20 | mapping/sorting uncovered  |
| all six `features/todos/hooks/*` | 0 | - | 0 | 0 | every hook at 0%              |
| `src/features/todos/utils/todos.ts` | 55.55 | 33.33 | 66.66 | 52 | filters/sorting partially    |
| `src/hooks/useNotice.ts`        | 54.54 | 75 | 40 | 71.42 | timer branch uncovered         |
| `src/lib/http.ts`               |     0 |      0 |     0 |     0 | no test                        |
| **All files**                   | 46.42 | 43.79 | 40.25 | 47.68 |                              |

The design system is excluded from coverage on purpose (`vite.config.ts`), and
its components are mocked through `src/design-system/mocks.tsx` in component
tests.

## Backfill targets

Highest value, lowest coverage, in the order the backfill workflow will pick
them up:

1. Backend: `core/config.py`, `core/lifespan.py`, `factory.py`, `api/health.py`
   (all 0%), then `repository.py` (40%) and `router.py` (51%).
2. Frontend: `lib/http.ts`, `src/features/todos/api/todos.ts`,
   `src/hooks/useNotice.ts`, `components/TodoEmptyState.tsx`,
   `components/TodoList.tsx` and the six hooks.

`backend/tests/mocks.py` (`create_autospec(TodoRepository)`) and
`frontend/src/design-system/mocks.tsx` are the established mocking boundaries;
new tests should follow them rather than introducing new patterns.
