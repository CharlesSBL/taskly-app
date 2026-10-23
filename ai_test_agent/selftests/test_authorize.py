from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from publisher.authorize import (
    AuthorizationError,
    authorize,
    is_authorized,
    labeler_permission,
)
from publisher.runner import RunResult


class FakeRunner:
    def __init__(self, result: RunResult) -> None:
        self.result = result
        self.calls: list[list[str]] = []

    def run(self, args: Sequence[str], cwd: Path | None = None) -> RunResult:
        self.calls.append(list(args))
        return self.result


def responder(permission: str) -> FakeRunner:
    return FakeRunner(RunResult(0, json.dumps({"permission": permission})))


@pytest.mark.parametrize("permission", ["admin", "write"])
def test_admin_and_write_are_authorized(permission: str) -> None:
    runner = responder(permission)
    assert labeler_permission(runner, "o/r", "alice") == permission
    authorize(runner, "o/r", "alice")
    assert runner.calls[0] == ["gh", "api", "repos/o/r/collaborators/alice/permission"]


@pytest.mark.parametrize("permission", ["read", "triage", "maintain", "none"])
def test_other_permissions_are_rejected(permission: str) -> None:
    assert not is_authorized(permission)
    with pytest.raises(AuthorizationError, match="admin or write"):
        authorize(responder(permission), "o/r", "bob")


def test_api_failure_fails_closed() -> None:
    runner = FakeRunner(RunResult(1, "", "Not Found"))
    assert labeler_permission(runner, "o/r", "eve") == "none"
    with pytest.raises(AuthorizationError):
        authorize(runner, "o/r", "eve")


def test_malformed_responses_fail_closed() -> None:
    assert labeler_permission(FakeRunner(RunResult(0, "not json")), "o/r", "x") == "none"
    assert labeler_permission(FakeRunner(RunResult(0, "[]")), "o/r", "x") == "none"
    assert (
        labeler_permission(FakeRunner(RunResult(0, json.dumps({"permission": 3}))), "o/r", "x")
        == "none"
    )
    assert labeler_permission(FakeRunner(RunResult(0, "")), "o/r", "x") == "none"
