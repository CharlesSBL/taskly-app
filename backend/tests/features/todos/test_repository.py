from datetime import datetime, timezone
from unittest.mock import Mock

from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

import app.features.todos.repository as repository_module
from app.features.todos.models import TodoRecord
from app.features.todos.repository import TodoRepository
from app.features.todos.schemas import Priority, TodoCreate, TodoUpdate

FROZEN_NOW = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return FROZEN_NOW


def freeze_clock(monkeypatch):
    monkeypatch.setattr(repository_module, "datetime", FrozenDatetime)
    return FROZEN_NOW


def test_list_maps_models_and_orders_tasks_newest_first(model_factory, todo_values, todo):
    session = Mock(spec=Session)
    session.scalars.return_value = [model_factory(todo_values)]
    assert TodoRepository(session).list() == [todo]
    statement = session.scalars.call_args.args[0]
    expected = select(TodoRecord).order_by(TodoRecord.created_at.desc(), TodoRecord.id.desc())
    assert statement.compare(expected)
    compiled = str(statement.compile(dialect=postgresql.dialect()))
    assert "ORDER BY todos.created_at DESC, todos.id DESC" in compiled


def test_get_returns_the_mapped_task(model_factory, todo_values, todo):
    session = Mock(spec=Session)
    session.get.return_value = model_factory(todo_values)

    assert TodoRepository(session).get(7) == todo

    session.get.assert_called_once_with(TodoRecord, 7)


def test_get_returns_none_for_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None
    assert TodoRepository(session).get(404) is None
    session.get.assert_called_once_with(TodoRecord, 404)


def test_create_persists_the_payload_with_shared_timestamps(monkeypatch, todo_values):
    freeze_clock(monkeypatch)
    session = Mock(spec=Session)
    session.refresh.side_effect = lambda record: setattr(record, "id", todo_values["id"])

    created = TodoRepository(session).create(
        TodoCreate(title="Plan the sprint", description="First scenario", priority="high")
    )

    record = session.add.call_args.args[0]
    assert isinstance(record, TodoRecord)
    assert (record.title, record.description) == ("Plan the sprint", "First scenario")
    assert record.priority is Priority.high
    assert record.created_at == FROZEN_NOW
    assert record.updated_at == FROZEN_NOW
    assert created.id == todo_values["id"]
    assert created.title == "Plan the sprint"
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(record)


def test_update_applies_only_the_provided_fields(monkeypatch, model_factory, todo_values, todo):
    freeze_clock(monkeypatch)
    session = Mock(spec=Session)
    record = model_factory(todo_values)
    session.get.return_value = record

    updated = TodoRepository(session).update(7, TodoUpdate(title="Renamed task"))

    assert record.title == "Renamed task"
    assert record.description == todo_values["description"]
    assert record.priority == Priority.high
    assert record.updated_at == FROZEN_NOW
    assert updated.title == "Renamed task"
    assert updated.updated_at == FROZEN_NOW
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(record)


def test_update_returns_none_for_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None

    assert TodoRepository(session).update(404, TodoUpdate(title="Renamed task")) is None

    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_delete_removes_the_task_and_reports_success(model_factory, todo_values):
    session = Mock(spec=Session)
    record = model_factory(todo_values)
    session.get.return_value = record

    assert TodoRepository(session).delete(7) is True

    session.delete.assert_called_once_with(record)
    session.commit.assert_called_once_with()


def test_delete_reports_a_missing_task():
    session = Mock(spec=Session)
    session.get.return_value = None

    assert TodoRepository(session).delete(404) is False

    session.delete.assert_not_called()
    session.commit.assert_not_called()
