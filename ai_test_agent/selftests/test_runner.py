from __future__ import annotations

from publisher.runner import SubprocessRunner


def test_success_and_failure() -> None:
    runner = SubprocessRunner(timeout=10)
    success = runner.run(["sh", "-c", "echo hello"])
    assert success.succeeded
    assert success.stdout.strip() == "hello"

    failure = runner.run(["sh", "-c", "echo boom >&2; exit 3"])
    assert failure.returncode == 3
    assert "boom" in failure.stderr


def test_missing_command_is_reported() -> None:
    result = SubprocessRunner(timeout=10).run(["definitely-not-a-command-xyz"])
    assert result.returncode == 127
    assert not result.succeeded


def test_timeout_is_reported() -> None:
    result = SubprocessRunner(timeout=0.2).run(["sleep", "5"])
    assert result.returncode == 124
    assert "timed out" in result.stderr
