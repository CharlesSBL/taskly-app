from datetime import date, timedelta

import pytest

from app.features.todos.schemas import TodoCreate


def test_list_returns_tasks_from_repository(client, repository_mock, todo):
    repository_mock.list.return_value = [todo]
    response = client.get("/api/todos")
    assert response.status_code == 200
    assert response.json() == [todo.model_dump(mode="json")]
    repository_mock.list.assert_called_once_with()


def test_due_soon_returns_only_tasks_inside_the_window(client, repository_mock, todo):
    today = date(2026, 10, 1)
    due_today = todo.model_copy(update={"id": 1, "due_date": today})
    due_on_boundary = todo.model_copy(
        update={"id": 2, "due_date": today + timedelta(days=3)}
    )
    too_far = todo.model_copy(update={"id": 3, "due_date": today + timedelta(days=4)})
    overdue = todo.model_copy(update={"id": 4, "due_date": today - timedelta(days=1)})
    no_due_date = todo.model_copy(update={"id": 5, "due_date": None})
    repository_mock.list.return_value = [
        due_today,
        due_on_boundary,
        too_far,
        overdue,
        no_due_date,
    ]
    response = client.get(
        "/api/todos/due-soon", params={"today": today.isoformat()}
    )
    assert response.status_code == 200
    assert response.json() == [
        due_today.model_dump(mode="json"),
        due_on_boundary.model_dump(mode="json"),
    ]
    repository_mock.list.assert_called_once_with()


def test_due_soon_honours_the_days_parameter(client, repository_mock, todo):
    today = date(2026, 10, 1)
    in_a_week = todo.model_copy(update={"due_date": today + timedelta(days=5)})
    repository_mock.list.return_value = [in_a_week]
    response = client.get(
        "/api/todos/due-soon", params={"today": today.isoformat(), "days": 7}
    )
    assert response.status_code == 200
    assert response.json() == [in_a_week.model_dump(mode="json")]


def test_due_soon_defaults_to_three_days_from_today(client, repository_mock, todo):
    today = date.today()
    due_today = todo.model_copy(update={"id": 1, "due_date": today})
    due_next_week = todo.model_copy(
        update={"id": 2, "due_date": today + timedelta(days=4)}
    )
    repository_mock.list.return_value = [due_today, due_next_week]
    response = client.get("/api/todos/due-soon")
    assert response.status_code == 200
    assert response.json() == [due_today.model_dump(mode="json")]


@pytest.mark.parametrize("days", [0, -1, 31])
def test_due_soon_rejects_days_outside_the_allowed_range(
    client, repository_mock, days
):
    response = client.get("/api/todos/due-soon", params={"days": days})
    assert response.status_code == 422
    repository_mock.list.assert_not_called()


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
