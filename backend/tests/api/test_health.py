from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_repository
from app.api.health import router as health_router
from app.features.todos.models import TodoRecord


@pytest.fixture
def health_repository(repository_mock):
    repository_mock.session = Mock(spec=Session)
    return repository_mock


@pytest.fixture
def health_client(health_repository):
    app = FastAPI()
    app.include_router(health_router)
    app.dependency_overrides[get_repository] = lambda: health_repository
    with TestClient(app) as client:
        yield client


def test_health_returns_ok_status(health_client):
    response = health_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_executes_a_single_probe_statement(health_client, health_repository):
    health_client.get("/api/health")

    health_repository.session.execute.assert_called_once()
    statement = health_repository.session.execute.call_args.args[0]
    assert statement.compare(select(TodoRecord.id).limit(1))


def test_health_propagates_database_failure(health_client, health_repository):
    health_repository.session.execute.side_effect = RuntimeError("database unavailable")

    with pytest.raises(RuntimeError, match="database unavailable"):
        health_client.get("/api/health")
