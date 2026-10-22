from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import create_database_engine, create_session_factory, initialize


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_database_engine(app.state.database_url)
    try:
        initialize(engine)
        app.state.session_factory = create_session_factory(engine)
        yield
    finally:
        engine.dispose()
