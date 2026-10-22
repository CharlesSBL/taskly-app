from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.features.todos.router import router
from app.features.todos.models import TodoRecord
from app.features.todos.schemas import Todo
from tests.mocks import make_repository_mock


@pytest.fixture
def repository_mock():
    return make_repository_mock()


@pytest.fixture
def client(repository_mock):
    # Mount just this router: factory, lifespan and health remain untested.
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_repository] = lambda: repository_mock
    with TestClient(app) as client:
        yield client


@pytest.fixture
def todo_values():
    return {
        "id": 7,
        "title": "Plan the sprint",
        "description": "First scenario",
        "priority": "high",
        "due_date": None,
        "completed": False,
        "created_at": datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 10, 1, 12, tzinfo=timezone.utc),
    }


@pytest.fixture
def todo(todo_values):
    return Todo.model_validate(todo_values)


@pytest.fixture
def model_factory():
    return lambda values: TodoRecord(**values)
