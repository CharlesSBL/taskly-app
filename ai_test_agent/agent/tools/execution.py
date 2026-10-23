"""Execute tests only through the hardened sandbox."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ..manifest import Stack
from ..tracing import truncate

MAX_COMMAND_OUTPUT = 8000
DEFAULT_TIMEOUT_SECONDS = 600
SAFE_ENV_KEYS = (
    "PATH",
    "HOME",
    "TMPDIR",
    "DOCKER_HOST",
    "DOCKER_CONFIG",
    "DOCKER_CERT_PATH",
    "DOCKER_TLS_VERIFY",
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


class SandboxRunner(Protocol):
    """Anything that can run a stack's tests in isolation."""

    def run(
        self, stack: Stack, paths: Sequence[str], *, coverage: bool = False
    ) -> CommandResult: ...


@dataclass(frozen=True)
class SubprocessSandbox:
    """Runs `sandbox/run.sh`, which applies the container security controls."""

    repo_root: Path
    script: Path
    out_dir: Path
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    def run(self, stack: Stack, paths: Sequence[str], *, coverage: bool = False) -> CommandResult:
        command = [
            str(self.script),
            "--stack",
            stack,
            "--repo",
            str(self.repo_root),
            "--out",
            str(self.out_dir),
            "--mode",
            "coverage" if coverage else "tests",
        ]
        if paths:
            command.append("--")
            command.extend(paths)

        environment = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", "replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", "replace")
            combined = stdout + stderr
            return CommandResult(returncode=124, output=truncate(combined, MAX_COMMAND_OUTPUT))

        return CommandResult(
            returncode=completed.returncode,
            output=truncate(completed.stdout + completed.stderr, MAX_COMMAND_OUTPUT),
        )
