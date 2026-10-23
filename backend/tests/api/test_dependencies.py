from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.api.dependencies import get_repository
from app.features.todos.repository import TodoRepository


def build_request(session_factory):
    app = SimpleNamespace(state=SimpleNamespace(session_factory=session_factory))
    return Request({"type": "http", "app": app})


def test_session_creation_failure_propagates_from_repository_dependency():
    session_factory = Mock(side_effect=RuntimeError("Session unavailable"))
    request = build_request(session_factory)
    dependency = get_repository(request)
    with pytest.raises(RuntimeError, match="Session unavailable"):
        next(dependency)
    session_factory.assert_called_once_with()


def test_dependency_yields_a_repository_bound_to_the_session_and_closes_it():
    session = Mock(spec=Session)
    session_factory = Mock(return_value=session)
    dependency = get_repository(build_request(session_factory))

    repository = next(dependency)

    assert isinstance(repository, TodoRepository)
    assert repository.session is session
    with pytest.raises(StopIteration):
        next(dependency)
    session.close.assert_called_once_with()
    session.rollback.assert_not_called()


def test_dependency_rolls_back_and_closes_when_the_request_fails():
    session = Mock(spec=Session)
    dependency = get_repository(build_request(Mock(return_value=session)))

    next(dependency)
    with pytest.raises(RuntimeError, match="commit failed"):
        dependency.throw(RuntimeError("commit failed"))

    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
