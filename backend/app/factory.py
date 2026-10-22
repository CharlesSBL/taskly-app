from fastapi import FastAPI

from .api.health import router as health_router
from .core.config import resolve_database_url
from .core.lifespan import lifespan
from .features.todos.router import router as todos_router


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="Taskly API", version="1.0.0", lifespan=lifespan)
    app.state.database_url = resolve_database_url(database_url)
    app.include_router(health_router)
    app.include_router(todos_router)
    return app
