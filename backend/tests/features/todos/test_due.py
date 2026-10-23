from datetime import date, timedelta

import pytest

from app.features.todos.due import is_due_within

TODAY = date(2026, 10, 1)


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (0, True),
        (1, True),
        (3, True),
        (4, False),
        (-1, False),
    ],
)
def test_due_date_counts_inside_the_window_only(offset, expected):
    assert is_due_within(TODAY + timedelta(days=offset), TODAY) is expected


def test_missing_due_date_is_never_due():
    assert is_due_within(None, TODAY) is False


def test_negative_window_is_never_due():
    assert is_due_within(TODAY, TODAY, days=-1) is False


def test_custom_window_extends_the_boundary():
    assert is_due_within(TODAY + timedelta(days=5), TODAY, days=5) is True
    assert is_due_within(TODAY + timedelta(days=6), TODAY, days=5) is False
