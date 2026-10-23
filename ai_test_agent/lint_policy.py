"""The lint bar applied to generated backend tests.

One module so the agent's writer, the agent's `run_lint` tool and the
verifier gate cannot drift: the gate stays authoritative, and the earlier the
agent sees the same rule the cheaper a rejection is.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

MAX_LINE_LENGTH = 100
RUFF_SELECT = "E,F,B"
LINT_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class LintResult:
    returncode: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0


def ruff_binary() -> str:
    found = shutil.which("ruff")
    if found:
        return found
    # The tooling venv's scripts directory is the reliable fallback when the
    # process is started as `.venv/bin/python -m ...`.
    candidate = Path(sys.executable).with_name("ruff")
    return str(candidate) if candidate.exists() else "ruff"


def ruff_arguments(files: Sequence[str]) -> list[str]:
    return [
        "check",
        "--isolated",
        "--select",
        RUFF_SELECT,
        "--line-length",
        str(MAX_LINE_LENGTH),
        *files,
    ]


def run_ruff(repo_dir: Path, files: Sequence[str]) -> LintResult:
    try:
        completed = subprocess.run(
            [ruff_binary(), *ruff_arguments(files)],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=LINT_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        return LintResult(returncode=127, output="ruff is not installed")
    except subprocess.TimeoutExpired:
        return LintResult(returncode=124, output="ruff timed out")
    return LintResult(
        returncode=completed.returncode,
        output=(completed.stdout + completed.stderr)[:2000],
    )
