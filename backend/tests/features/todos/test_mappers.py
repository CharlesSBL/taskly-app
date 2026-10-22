from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.features.todos.mappers import from_model


@pytest.mark.parametrize("completed", [False, True])
def test_maps_orm_values_without_mutating_the_model(model_factory, todo_values, completed):
    values = {**todo_values, "completed": completed, "due_date": date(2026, 10, 15)}
    record = model_factory(values)
    todo = from_model(record)
    assert todo.id == values["id"]
    assert todo.title == values["title"]
    assert todo.description == values["description"]
    assert todo.priority == "high"
    assert todo.completed is completed
    assert todo.due_date == date(2026, 10, 15)
    assert todo.created_at == datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
    assert todo.updated_at == todo.created_at
    assert {field: getattr(record, field) for field in values} == values


def test_maps_a_missing_due_date(model_factory, todo_values):
    assert from_model(model_factory(todo_values)).due_date is None


def test_rejects_invalid_stored_data(model_factory, todo_values):
    with pytest.raises(ValidationError, match="title"):
        from_model(model_factory({**todo_values, "title": ""}))
