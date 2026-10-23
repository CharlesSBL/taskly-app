from datetime import date, timedelta


def is_due_within(due_date: date | None, today: date, days: int = 3) -> bool:
    """Return True when a task is due between today and today + days."""
    if due_date is None or days < 0:
        return False
    return today <= due_date <= today + timedelta(days=days)
