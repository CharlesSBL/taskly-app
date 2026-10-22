from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from .mappers import from_model
from .models import TodoRecord
from .schemas import Todo, TodoCreate, TodoUpdate


class TodoRepository:
    def __init__(self, session: Session):
        self.session = session

    def list(self) -> list[Todo]:
        statement = select(TodoRecord).order_by(TodoRecord.created_at.desc(), TodoRecord.id.desc())
        return [from_model(record) for record in self.session.scalars(statement)]

    def get(self, todo_id: int) -> Todo | None:
        record = self.session.get(TodoRecord, todo_id)
        return from_model(record) if record is not None else None

    def create(self, payload: TodoCreate) -> Todo:
        now = datetime.now(timezone.utc)
        record = TodoRecord(**payload.model_dump(), created_at=now, updated_at=now)
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return from_model(record)

    def update(self, todo_id: int, payload: TodoUpdate) -> Todo | None:
        record = self.session.get(TodoRecord, todo_id)
        if record is None:
            return None
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        record.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(record)
        return from_model(record)

    def delete(self, todo_id: int) -> bool:
        record = self.session.get(TodoRecord, todo_id)
        if record is None:
            return False
        self.session.delete(record)
        self.session.commit()
        return True
