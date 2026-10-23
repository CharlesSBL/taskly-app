from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path

from agent.manifest import Decision, Manifest
from verifier.differential import DifferentialConfig, check_on_base
from verifier.sandbox import CommandResult

BASE_SOURCE = "def add(a, b):\n    return a + b\n"
PR_TEST = "from app.feature import add\n\ndef test_add():\n    assert add(1, 2) == 3\n"


class RepoAwareSandbox:
    def __init__(self, pr_dir: Path, base_result: CommandResult) -> None:
        self.pr_dir = pr_dir
        self.base_result = base_result
        self.calls: list[tuple[str, list[str], Path | None]] = []

    def run(
        self,
        stack: str,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
        repo: Path | None = None,
    ) -> CommandResult:
        self.calls.append((stack, list(paths), repo))
        if repo is not None and repo != self.pr_dir:
            return self.base_result
        return CommandResult(0, "1 passed")


def make_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "base"
    (repo / "backend/app").mkdir(parents=True)
    (repo / "backend/tests").mkdir(parents=True)
    (repo / "backend/app/feature.py").write_text(BASE_SOURCE)
    (repo / "backend/tests/__init__.py").write_text("")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
    return repo


def make_pr(tmp_path: Path) -> Path:
    pr = tmp_path / "pr"
    (pr / "backend/tests").mkdir(parents=True)
    (pr / "backend/tests/test_feature.py").write_text(PR_TEST)
    return pr


def manifest_for(target: str, source: str = "backend/app/feature.py") -> Manifest:
    return Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        decisions=[
            Decision(
                file=source,
                action="update",
                rationale="new branch",
                target_test_file=target,
            )
        ],
        files_written=[target],
    )


def head_sha(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_failure_on_base_is_reported(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    pr = make_pr(tmp_path)
    target = "backend/tests/test_feature.py"
    sandbox = RepoAwareSandbox(pr, CommandResult(1, "1 failed"))

    result = check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha=head_sha(repo),
            pr_dir=pr,
            manifest=manifest_for(target),
            sandbox=sandbox,
        ),
        [target],
    )

    assert result == {target: "true"}
    assert sandbox.calls[-1][1] == ["tests/test_feature.py"]
    assert sandbox.calls[-1][2] != pr


def test_pass_on_base_is_reported(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    pr = make_pr(tmp_path)
    target = "backend/tests/test_feature.py"
    sandbox = RepoAwareSandbox(pr, CommandResult(0, "1 passed"))
    result = check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha=head_sha(repo),
            pr_dir=pr,
            manifest=manifest_for(target),
            sandbox=sandbox,
        ),
        [target],
    )
    assert result == {target: "false"}


def test_new_source_file_is_not_applicable(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    pr = make_pr(tmp_path)
    target = "backend/tests/test_feature.py"
    sandbox = RepoAwareSandbox(pr, CommandResult(1, "failed"))
    result = check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha=head_sha(repo),
            pr_dir=pr,
            manifest=manifest_for(target, source="backend/app/new_module.py"),
            sandbox=sandbox,
        ),
        [target],
    )
    assert result == {target: "n/a"}
    assert sandbox.calls == []


def test_invalid_base_sha_marks_everything_not_applicable(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    pr = make_pr(tmp_path)
    target = "backend/tests/test_feature.py"
    sandbox = RepoAwareSandbox(pr, CommandResult(1, "failed"))
    result = check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha="0" * 40,
            pr_dir=pr,
            manifest=manifest_for(target),
            sandbox=sandbox,
        ),
        [target],
    )
    assert result == {target: "n/a"}


def test_worktree_is_removed(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    pr = make_pr(tmp_path)
    target = "backend/tests/test_feature.py"
    check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha=head_sha(repo),
            pr_dir=pr,
            manifest=manifest_for(target),
            sandbox=RepoAwareSandbox(pr, CommandResult(1, "failed")),
        ),
        [target],
    )
    listing = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list"], capture_output=True, text=True, check=True
    ).stdout
    assert "taskly-base-" not in listing
    assert repo.name in listing


def test_empty_file_list(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    result = check_on_base(
        DifferentialConfig(
            trusted_dir=repo,
            base_sha=head_sha(repo),
            pr_dir=tmp_path,
            manifest=manifest_for("backend/tests/test_feature.py"),
            sandbox=RepoAwareSandbox(tmp_path, CommandResult(1, "failed")),
        ),
        [],
    )
    assert result == {}
