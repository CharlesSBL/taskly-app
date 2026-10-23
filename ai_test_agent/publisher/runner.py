"""Thin, injectable wrapper around subprocess for git and gh."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RunResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class Runner(Protocol):
    def run(self, args: Sequence[str], cwd: Path | None = None) -> RunResult: ...


@dataclass(frozen=True)
class SubprocessRunner:
    timeout: float = 120

    def run(self, args: Sequence[str], cwd: Path | None = None) -> RunResult:
        try:
            completed = subprocess.run(
                list(args),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as exc:
            return RunResult(returncode=127, stderr=str(exc))
        except subprocess.TimeoutExpired:
            return RunResult(returncode=124, stderr="command timed out")
        return RunResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
