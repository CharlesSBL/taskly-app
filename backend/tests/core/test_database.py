from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect

from app.core.database import create_database_engine, create_session_factory, initialize
from app.features.todos.models import TodoRecord

CREATED_AT = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def make_sqlite_engine():
    return create_engine("sqlite+pysqlite:///:memory:")


def make_record(title="Plan the sprint"):
    return TodoRecord(title=title, created_at=CREATED_AT, updated_at=CREATED_AT)


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


def test_initialize_creates_the_todos_table():
    engine = make_sqlite_engine()
    try:
        initialize(engine)

        assert inspect(engine).get_table_names() == ["todos"]
    finally:
        engine.dispose()


def test_initialize_tolerates_an_already_migrated_schema():
    engine = make_sqlite_engine()
    try:
        initialize(engine)
        initialize(engine)

        assert inspect(engine).get_table_names() == ["todos"]
    finally:
        engine.dispose()


def test_session_factory_binds_sessions_to_the_engine_and_persists_records():
    engine = make_sqlite_engine()
    try:
        initialize(engine)
        factory = create_session_factory(engine)

        with factory() as session:
            assert session.get_bind() is engine
            session.add(make_record())
            session.commit()

        with factory() as session:
            stored = session.get(TodoRecord, 1)
            assert stored is not None
            assert stored.title == "Plan the sprint"
            assert stored.completed is False
            assert stored.description == ""
    finally:
        engine.dispose()


def test_session_factory_keeps_attributes_loaded_after_commit():
    engine = make_sqlite_engine()
    try:
        initialize(engine)
        with create_session_factory(engine)() as session:
            record = make_record()
            session.add(record)
            session.commit()

            assert inspect(record).expired is False
            assert record.title == "Plan the sprint"
            assert record.id == 1
    finally:
        engine.dispose()
