from datetime import date

import pytest
from pydantic import ValidationError

from app.features.todos.schemas import TodoUpdate
from app.features.todos.validators import validate_patch_fields


def test_rejects_an_empty_patch():
    with pytest.raises(ValidationError, match="Provide at least one field"):
        TodoUpdate()


@pytest.mark.parametrize("field", ["title", "description", "priority", "completed"])
def test_rejects_explicit_null_for_non_nullable_fields(field):
    with pytest.raises(ValidationError, match=f"Field {field} cannot be null"):
        TodoUpdate(**{field: None})


def test_allows_clearing_only_the_due_date():
    patch = TodoUpdate(due_date=None)
    assert validate_patch_fields(patch) is patch
    assert patch.model_dump(exclude_unset=True) == {"due_date": None}


def test_preserves_every_non_null_patch_field():
    patch = TodoUpdate(
        title="  Renamed task  ", description="  Details  ", priority="low",
        completed=False, due_date="2026-10-15",
    )
    assert validate_patch_fields(patch) is patch
    assert patch.model_dump(exclude_unset=True) == {
        "title": "Renamed task", "description": "Details", "priority": "low",
        "completed": False, "due_date": date(2026, 10, 15),
    }
