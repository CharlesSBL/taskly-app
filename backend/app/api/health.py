from fastapi import APIRouter
from sqlalchemy import select

from ..features.todos.models import TodoRecord
from .dependencies import Repository

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(repo: Repository):
    repo.session.execute(select(TodoRecord.id).limit(1))
    return {"status": "ok"}
