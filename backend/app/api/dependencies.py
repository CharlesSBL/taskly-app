from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from ..features.todos.repository import TodoRepository


def get_repository(request: Request) -> Iterator[TodoRepository]:
    session = request.app.state.session_factory()
    try:
        yield TodoRepository(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


Repository = Annotated[TodoRepository, Depends(get_repository)]
