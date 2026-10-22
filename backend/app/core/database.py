from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..features.todos.models import Base


def create_database_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 10},
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def initialize(engine: Engine) -> None:
    Base.metadata.create_all(engine)
