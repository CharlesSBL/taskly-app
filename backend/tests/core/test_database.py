from unittest.mock import Mock

from sqlalchemy import Engine, create_engine, inspect

from app.core.database import (
    create_database_engine,
    create_session_factory,
    initialize,
)


def test_engine_uses_the_postgresql_psycopg_driver():
    url = "postgresql+psycopg://taskly:taskly@localhost:5432/taskly"
    engine = create_database_engine(url)
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert engine.url.database == "taskly"
    finally:
        engine.dispose()


def test_session_factory_binds_the_engine_and_keeps_attributes_after_commit():
    engine = Mock(spec=Engine)

    factory = create_session_factory(engine)
    session = factory()
    try:
        assert session.bind is engine
        assert session.expire_on_commit is False
    finally:
        session.close()


def test_initialize_creates_the_todos_table():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        initialize(engine)

        assert "todos" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_initialize_is_idempotent_for_an_existing_schema():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        initialize(engine)
        initialize(engine)

        assert inspect(engine).get_table_names().count("todos") == 1
    finally:
        engine.dispose()
