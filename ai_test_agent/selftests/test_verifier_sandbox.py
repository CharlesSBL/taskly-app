from __future__ import annotations

from pathlib import Path

import pytest

from verifier.sandbox import SubprocessSandbox


def script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "fake.sh"
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def test_modes_are_forwarded(tmp_path: Path) -> None:
    sandbox = SubprocessSandbox(script=script(tmp_path, 'echo "$@"'), out_dir=tmp_path)
    result = sandbox.run("backend", ["tests/test_a.py"], repo=tmp_path)
    assert result.succeeded
    assert "--mode tests" in result.output
    assert "tests/test_a.py" in result.output

    coverage = sandbox.run("backend", [], coverage=True, repo=tmp_path)
    assert "--mode coverage" in coverage.output

    typecheck = sandbox.run("frontend", [], typecheck=True, repo=tmp_path)
    assert "--mode typecheck" in typecheck.output


def test_repo_is_required(tmp_path: Path) -> None:
    sandbox = SubprocessSandbox(script=script(tmp_path, "true"), out_dir=tmp_path)
    with pytest.raises(ValueError, match="repo is required"):
        sandbox.run("backend", [])


def test_failure_output_is_returned(tmp_path: Path) -> None:
    sandbox = SubprocessSandbox(script=script(tmp_path, "echo boom >&2; exit 3"), out_dir=tmp_path)
    result = sandbox.run("frontend", [], repo=tmp_path)
    assert result.returncode == 3
    assert "boom" in result.output
    assert not result.succeeded


def test_timeout_is_reported(tmp_path: Path) -> None:
    sandbox = SubprocessSandbox(script=script(tmp_path, "sleep 5"), out_dir=tmp_path, timeout=0.2)
    result = sandbox.run("backend", [], repo=tmp_path)
    assert result.returncode == 124
    assert "timed out" in result.output
