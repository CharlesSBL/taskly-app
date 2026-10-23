from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response

from ...api.dependencies import Repository
from .due import is_due_within
from .schemas import Todo, TodoCreate, TodoUpdate

router = APIRouter(prefix="/api/todos", tags=["todos"])
TodoId = Annotated[int, Path(gt=0)]


@router.get("", response_model=list[Todo])
def list_todos(repo: Repository):
    return repo.list()


@router.get("/due-soon", response_model=list[Todo])
def list_due_soon(
    repo: Repository,
    days: Annotated[int, Query(ge=1, le=30)] = 3,
    today: date | None = None,
):
    reference = today or date.today()
    return [todo for todo in repo.list() if is_due_within(todo.due_date, reference, days)]


@router.post("", response_model=Todo, status_code=201)
def create_todo(payload: TodoCreate, repo: Repository):
    return repo.create(payload)


@router.get("/{todo_id}", response_model=Todo)
def get_todo(todo_id: TodoId, repo: Repository):
    todo = repo.get(todo_id)
    if todo is None:
        raise HTTPException(404, "Task not found.")
    return todo


@router.patch("/{todo_id}", response_model=Todo)
def update_todo(todo_id: TodoId, payload: TodoUpdate, repo: Repository):
    todo = repo.update(todo_id, payload)
    if todo is None:
        raise HTTPException(404, "Task not found.")
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: TodoId, repo: Repository):
    if not repo.delete(todo_id):
        raise HTTPException(404, "Task not found.")
    return Response(status_code=204)
