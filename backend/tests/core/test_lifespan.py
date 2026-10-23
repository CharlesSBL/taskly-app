import asyncio
from unittest.mock import Mock

import pytest
from fastapi import FastAPI

import app.core.lifespan as lifespan_module

DATABASE_URL = "postgresql+psycopg://taskly:taskly@localhost:5432/taskly"  # pragma: allowlist secret


@pytest.fixture
def app():
    app = FastAPI()
    app.state.database_url = DATABASE_URL
    return app


@pytest.fixture
def engine():
    return Mock()


@pytest.fixture
def engine_factory(monkeypatch, engine):
    factory = Mock(return_value=engine)
    monkeypatch.setattr(lifespan_module, "create_database_engine", factory)
    return factory


@pytest.fixture
def initialize(monkeypatch):
    initialize = Mock()
    monkeypatch.setattr(lifespan_module, "initialize", initialize)
    return initialize


@pytest.fixture
def session_factory(monkeypatch):
    session_factory = Mock()
    monkeypatch.setattr(
        lifespan_module, "create_session_factory", Mock(return_value=session_factory)
    )
    return session_factory


def run_lifespan(app, during_yield=None):
    async def scenario():
        async with lifespan_module.lifespan(app):
            if during_yield is not None:
                during_yield()

    asyncio.run(scenario())


def test_startup_builds_the_session_factory_and_disposes_the_engine(
    app, engine, engine_factory, initialize, session_factory
):
    run_lifespan(app)

    engine_factory.assert_called_once_with(DATABASE_URL)
    initialize.assert_called_once_with(engine)
    assert app.state.session_factory is session_factory
    engine.dispose.assert_called_once_with()


def test_failed_initialization_disposes_the_engine_without_a_session_factory(
    app, engine, engine_factory, monkeypatch
):
    monkeypatch.setattr(lifespan_module, "initialize", Mock(side_effect=RuntimeError("no db")))

    with pytest.raises(RuntimeError, match="no db"):
        run_lifespan(app)

    assert not hasattr(app.state, "session_factory")
    engine.dispose.assert_called_once_with()


def test_failure_during_serving_still_disposes_the_engine(
    app, engine, engine_factory, initialize, session_factory
):
    def fail():
        raise RuntimeError("request crashed")

    with pytest.raises(RuntimeError, match="request crashed"):
        run_lifespan(app, during_yield=fail)

    engine.dispose.assert_called_once_with()
