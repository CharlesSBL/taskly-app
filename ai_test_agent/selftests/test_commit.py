from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from publisher.commit import (
    apply_verified_patch,
    is_allowed_path,
    patch_paths,
    patch_sha256,
)
from publisher.runner import RunResult

PATH = "backend/tests/test_feature.py"
PATCH = (
    f"diff --git a/{PATH} b/{PATH}\n"
    "new file mode 100644\n"
    "--- /dev/null\n"
    f"+++ b/{PATH}\n"
    "@@ -0,0 +1,2 @@\n"
    "+def test_x():\n"
    "+    assert 1 == 1\n"
)


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


def write_patch(tmp_path: Path, text: str = PATCH) -> Path:
    path = tmp_path / "verified_tests.patch"
    path.write_text(text, encoding="utf-8")
    return path


def test_happy_path_applies_commits_and_pushes(tmp_path: Path) -> None:
    patch_path = write_patch(tmp_path)
    runner = ScriptedRunner({"apply --numstat": RunResult(0, f"1\t0\t{PATH}\n")})

    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=patch_path,
        expected_sha=patch_sha256(PATCH),
        branch="ai-tests/demo",
        message="test: add feature tests",
    )

    assert outcome.ok, outcome.message
    joined = [" ".join(call) for call in runner.calls]
    assert any("apply --check" in call for call in joined)
    assert any("apply --whitespace=nowarn" in call for call in joined)
    assert any("add --" in call and PATH in call for call in joined)
    assert any("commit -m test: add feature tests" in call for call in joined)
    assert any("push origin HEAD:refs/heads/ai-tests/demo" in call for call in joined)


def test_sha_mismatch_fails_before_running_anything(tmp_path: Path) -> None:
    runner = ScriptedRunner()
    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=write_patch(tmp_path),
        expected_sha="0" * 64,
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "sha256 mismatch" in outcome.message
    assert runner.calls == []


def test_empty_or_missing_patch_is_rejected(tmp_path: Path) -> None:
    runner = ScriptedRunner()
    empty = write_patch(tmp_path, "")
    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=empty,
        expected_sha=patch_sha256(""),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "empty patch" in outcome.message

    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=tmp_path / "missing.patch",
        expected_sha="x",
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "not found" in outcome.message


def test_forbidden_paths_are_rejected(tmp_path: Path) -> None:
    target = ".github/workflows/x.yml"
    forbidden = f"diff --git a/{target} b/{target}\n--- /dev/null\n+++ b/{target}\n"
    outcome = apply_verified_patch(
        ScriptedRunner(),
        repo=tmp_path,
        patch_path=write_patch(tmp_path, forbidden),
        expected_sha=patch_sha256(forbidden),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "forbidden paths" in outcome.message


def test_patch_without_files_is_rejected(tmp_path: Path) -> None:
    text = "not a diff\n"
    outcome = apply_verified_patch(
        ScriptedRunner(),
        repo=tmp_path,
        patch_path=write_patch(tmp_path, text),
        expected_sha=patch_sha256(text),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "no files" in outcome.message


def test_numstat_mismatch_is_rejected(tmp_path: Path) -> None:
    runner = ScriptedRunner({"apply --numstat": RunResult(0, "1\t0\tbackend/tests/other.py\n")})
    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=write_patch(tmp_path),
        expected_sha=patch_sha256(PATCH),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "do not match" in outcome.message


def test_numstat_failure_is_rejected(tmp_path: Path) -> None:
    runner = ScriptedRunner({"apply --numstat": RunResult(1, "", "bad patch")})
    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=write_patch(tmp_path),
        expected_sha=patch_sha256(PATCH),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "numstat" in outcome.message


def test_apply_and_push_failures_are_reported(tmp_path: Path) -> None:
    patch_path = write_patch(tmp_path)
    numstat = {"apply --numstat": RunResult(0, f"1\t0\t{PATH}\n")}
    check_failure = ScriptedRunner({**numstat, "apply --check": RunResult(1, "", "does not apply")})
    assert (
        "does not apply"
        in apply_verified_patch(
            check_failure,
            repo=tmp_path,
            patch_path=patch_path,
            expected_sha=patch_sha256(PATCH),
            branch="b",
            message="m",
        ).message
    )

    push_failure = ScriptedRunner({**numstat, "push origin": RunResult(1, "", "rejected")})
    outcome = apply_verified_patch(
        push_failure,
        repo=tmp_path,
        patch_path=patch_path,
        expected_sha=patch_sha256(PATCH),
        branch="b",
        message="m",
    )
    assert not outcome.ok
    assert "git push failed" in outcome.message


def test_helpers() -> None:
    assert patch_paths(PATCH) == [PATH]
    assert is_allowed_path("backend/tests/test_x.py")
    assert is_allowed_path("frontend/src/lib/http.test.ts")
    assert not is_allowed_path("backend/tests/conftest.py")
    assert not is_allowed_path("../evil.py")
    assert not is_allowed_path("ai_test_agent/selftests/test_x.py")
    assert not is_allowed_path("frontend/src/lib/http.test.js")


def test_relative_patch_path_is_resolved_before_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Regression: git -C resolves a relative patch path against the repo.
    write_patch(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = ScriptedRunner({"apply --numstat": RunResult(0, f"1\t0\t{PATH}\n")})

    outcome = apply_verified_patch(
        runner,
        repo=tmp_path,
        patch_path=Path("verified_tests.patch"),
        expected_sha=patch_sha256(PATCH),
        branch="b",
        message="m",
    )

    assert outcome.ok, outcome.message
    joined = [" ".join(call) for call in runner.calls]
    assert any(str(tmp_path / "verified_tests.patch") in call for call in joined)
