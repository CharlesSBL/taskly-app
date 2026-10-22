from .models import TodoRecord
from .schemas import Todo


def from_model(record: TodoRecord) -> Todo:
    return Todo.model_validate(record, from_attributes=True)
