import pytest

from app.features.todos.schemas import TodoCreate, TodoUpdate


def test_list_returns_tasks_from_repository(client, repository_mock, todo):
    repository_mock.list.return_value = [todo]
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == [todo.model_dump(mode="json")]
    repository_mock.list.assert_called_once_with()


def test_create_trims_input_and_returns_created_task(client, repository_mock, todo):
    repository_mock.create.return_value = todo
    response = client.post("/api/todos", json={"title": "  Plan the sprint  ", "priority": "high"})
    assert response.status_code == 201
    assert response.json() == todo.model_dump(mode="json")
    repository_mock.create.assert_called_once_with(
        TodoCreate(title="Plan the sprint", priority="high")
    )


@pytest.mark.parametrize("payload", [
    {"title": "   "},
    {"title": "x" * 121},
    {"title": "Task", "priority": "urgent"},
    {"title": "Task", "due_date": "2026-02-30"},
])
def test_invalid_create_never_calls_repository(client, repository_mock, payload):
    assert client.post("/api/todos", json=payload).status_code == 422
    repository_mock.create.assert_not_called()


def test_get_returns_the_requested_task(client, repository_mock, todo):
    repository_mock.get.return_value = todo

    response = client.get("/api/todos/7")

    assert response.status_code == 200
    assert response.json() == todo.model_dump(mode="json")
    repository_mock.get.assert_called_once_with(7)


def test_get_missing_task_returns_404(client, repository_mock):
    repository_mock.get.return_value = None

    response = client.get("/api/todos/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_patch_applies_the_changes(client, repository_mock, todo):
    repository_mock.update.return_value = todo

    response = client.patch("/api/todos/7", json={"title": "Renamed task"})

    assert response.status_code == 200
    assert response.json() == todo.model_dump(mode="json")
    repository_mock.update.assert_called_once_with(7, TodoUpdate(title="Renamed task"))


def test_patch_missing_task_returns_404(client, repository_mock):
    repository_mock.update.return_value = None

    response = client.patch("/api/todos/404", json={"title": "Renamed task"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_delete_removes_the_task_without_a_body(client, repository_mock):
    repository_mock.delete.return_value = True

    response = client.delete("/api/todos/7")

    assert response.status_code == 204
    assert response.content == b""
    repository_mock.delete.assert_called_once_with(7)


def test_delete_missing_task_returns_404(client, repository_mock):
    repository_mock.delete.return_value = False

    response = client.delete("/api/todos/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


@pytest.mark.parametrize("todo_id", [0, -1])
def test_rejects_non_positive_todo_ids(client, repository_mock, todo_id):
    response = client.get(f"/api/todos/{todo_id}")

    assert response.status_code == 422
    repository_mock.get.assert_not_called()
