import asyncio
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from fastapi import FastAPI

import app.factory as factory_module

RESOLVED_URL = "postgresql+psycopg://taskly:taskly@localhost:5432/taskly"


@pytest.fixture
def resolver(monkeypatch):
    resolver = Mock(return_value=RESOLVED_URL)
    monkeypatch.setattr(factory_module, "resolve_database_url", resolver)
    return resolver


@pytest.mark.parametrize("database_url", [None, "postgresql+psycopg://override:secret@db:5432/x"])
def test_stores_the_resolved_database_url_on_app_state(database_url, resolver):
    application = factory_module.create_app(database_url)

    assert application.state.database_url == RESOLVED_URL
    resolver.assert_called_once_with(database_url)


def test_exposes_the_api_metadata(resolver):
    application = factory_module.create_app()

    assert isinstance(application, FastAPI)
    assert (application.title, application.version) == ("Taskly API", "1.0.0")


def test_mounts_the_health_and_todos_routes(resolver):
    application = factory_module.create_app()

    documented = application.openapi()["paths"]
    assert {"/api/health", "/api/todos", "/api/todos/{todo_id}"} <= set(documented)


def test_app_lifespan_runs_the_application_lifespan(resolver, monkeypatch):
    started = []

    @asynccontextmanager
    async def fake_lifespan(application):
        started.append(application)
        yield

    monkeypatch.setattr(factory_module, "lifespan", fake_lifespan)
    application = factory_module.create_app()

    async def scenario():
        async with application.router.lifespan_context(application):
            pass

    asyncio.run(scenario())

    assert started == [application]
