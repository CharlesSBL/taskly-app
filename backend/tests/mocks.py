from unittest.mock import create_autospec

from app.features.todos.repository import TodoRepository


def make_repository_mock():
    """Return a fresh, interface-checked mock shared by API tests."""
    repository = create_autospec(TodoRepository, instance=True)
    repository.list.return_value = []
    return repository
