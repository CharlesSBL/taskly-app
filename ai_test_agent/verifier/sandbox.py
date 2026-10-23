"""Sandbox runner used by the verifier.

Deliberately separate from the agent's runner: the gate must not share code
with the component whose output it verifies. Both call the same
`sandbox/run.sh`, so the security controls are identical.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agent.manifest import Stack

MAX_OUTPUT = 8000
DEFAULT_TIMEOUT = 600


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class SandboxRunner(Protocol):
    def run(
        self,
        stack: Stack,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
        repo: Path | None = None,
    ) -> CommandResult: ...


@dataclass(frozen=True)
class SubprocessSandbox:
    script: Path
    out_dir: Path
    timeout: float = DEFAULT_TIMEOUT

    def run(
        self,
        stack: Stack,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
        repo: Path | None = None,
    ) -> CommandResult:
        if typecheck:
            mode = "typecheck"
        elif coverage:
            mode = "coverage"
        else:
            mode = "tests"
        if repo is None:
            raise ValueError("repo is required")

        command = [
            str(self.script),
            "--stack",
            stack,
            "--repo",
            str(repo),
            "--out",
            str(self.out_dir),
            "--mode",
            mode,
        ]
        if paths:
            command.append("--")
            command.extend(paths)

        environment = {
            key: os.environ[key]
            for key in (
                "PATH",
                "HOME",
                "TMPDIR",
                "DOCKER_HOST",
                "DOCKER_CONFIG",
                "DOCKER_CERT_PATH",
                "DOCKER_TLS_VERIFY",
            )
            if key in os.environ
        }
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                env=environment,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(returncode=124, output="timed out waiting for the sandbox")
        return CommandResult(
            returncode=completed.returncode,
            output=(completed.stdout + completed.stderr)[:MAX_OUTPUT],
        )
