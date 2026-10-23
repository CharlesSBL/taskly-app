from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from publisher.backfill import open_backfill_pr
from publisher.runner import RunResult


class ScriptedRunner:
    def __init__(self, responses: dict[str, RunResult] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[list[str]] = []

    def run(self, args: Sequence[str], cwd: Path | None = None) -> RunResult:
        self.calls.append(list(args))
        joined = " ".join(args)
        for needle, result in self.responses.items():
            if needle in joined:
                return result
        return RunResult(0, "")


def body(tmp_path: Path) -> Path:
    path = tmp_path / "body.md"
    path.write_text("Coverage: 42% -> 51%")
    return path


def test_protected_branch_is_refused(tmp_path: Path) -> None:
    runner = ScriptedRunner()
    outcome = open_backfill_pr(
        runner,
        repo="o/r",
        repo_dir=tmp_path,
        branch="main",
        base_branch="main",
        title="t",
        body_path=body(tmp_path),
    )
    assert not outcome.ok
    assert "protected" in outcome.message
    assert runner.calls == []


def test_existing_pr_is_updated(tmp_path: Path) -> None:
    runner = ScriptedRunner({"pr list": RunResult(0, "42\n")})
    outcome = open_backfill_pr(
        runner,
        repo="o/r",
        repo_dir=tmp_path,
        branch="chore/ai-backfill-unit-tests",
        base_branch="main",
        title="Backfill",
        body_path=body(tmp_path),
    )
    assert outcome.ok, outcome.message
    assert any("pr edit 42" in " ".join(call) for call in runner.calls)
    assert not any("pr create" in " ".join(call) for call in runner.calls)


def test_new_pr_is_created(tmp_path: Path) -> None:
    runner = ScriptedRunner()
    outcome = open_backfill_pr(
        runner,
        repo="o/r",
        repo_dir=tmp_path,
        branch="chore/ai-backfill-unit-tests",
        base_branch="main",
        title="Backfill",
        body_path=body(tmp_path),
    )
    assert outcome.ok, outcome.message
    create = [call for call in runner.calls if "pr" in call and "create" in call]
    assert create
    assert "--base" in create[0]
    assert "main" in create[0]


def test_push_failure_is_reported(tmp_path: Path) -> None:
    runner = ScriptedRunner({"push": RunResult(1, "", "denied")})
    outcome = open_backfill_pr(
        runner,
        repo="o/r",
        repo_dir=tmp_path,
        branch="chore/ai-backfill-unit-tests",
        base_branch="main",
        title="Backfill",
        body_path=body(tmp_path),
    )
    assert not outcome.ok
    assert "git push failed" in outcome.message


def test_missing_body_is_rejected(tmp_path: Path) -> None:
    outcome = open_backfill_pr(
        ScriptedRunner(),
        repo="o/r",
        repo_dir=tmp_path,
        branch="chore/ai-backfill-unit-tests",
        base_branch="main",
        title="Backfill",
        body_path=tmp_path / "missing.md",
    )
    assert not outcome.ok
    assert "body not found" in outcome.message


def test_pr_edit_failure_is_reported(tmp_path: Path) -> None:
    runner = ScriptedRunner({"pr list": RunResult(0, "7"), "pr edit": RunResult(1, "", "boom")})
    outcome = open_backfill_pr(
        runner,
        repo="o/r",
        repo_dir=tmp_path,
        branch="chore/ai-backfill-unit-tests",
        base_branch="main",
        title="Backfill",
        body_path=body(tmp_path),
    )
    assert not outcome.ok
    assert "gh pr edit failed" in outcome.message
