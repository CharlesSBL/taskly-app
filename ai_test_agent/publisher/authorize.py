"""Authorize the human who applied the `ai-tests:commit` label.

Fail closed: an unreadable answer, a missing permission field, an API error or
a bot account all mean "not authorized". Only admin or write can commit.
"""

from __future__ import annotations

import json

from .runner import Runner

ALLOWED = {"admin", "write"}


class AuthorizationError(RuntimeError):
    pass


def labeler_permission(runner: Runner, repo: str, login: str) -> str:
    result = runner.run(["gh", "api", f"repos/{repo}/collaborators/{login}/permission"])
    if not result.succeeded or not result.stdout.strip():
        return "none"
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return "none"
    if not isinstance(payload, dict):
        return "none"
    permission = payload.get("permission")
    return permission if isinstance(permission, str) else "none"


def is_authorized(permission: str) -> bool:
    return permission in ALLOWED


def authorize(runner: Runner, repo: str, login: str) -> None:
    permission = labeler_permission(runner, repo, login)
    if not is_authorized(permission):
        raise AuthorizationError(
            f"{login} has permission {permission!r}; admin or write is required"
        )
