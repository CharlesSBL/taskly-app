"""Differential fail-on-base check.

Run the accepted tests against the BASE revision's source. A test that passes
on the base may not detect the regression the PR introduces; a test that fails
on the base is evidence that it exercises the new behavior. New source files do
not exist on the base and are reported as `n/a`, never as pass or fail.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agent.manifest import Manifest, Stack

from .sandbox import SandboxRunner

FAILED_ON_BASE = "true"
PASSED_ON_BASE = "false"
NOT_APPLICABLE = "n/a"


@dataclass(frozen=True)
class DifferentialConfig:
    trusted_dir: Path
    base_sha: str
    pr_dir: Path
    manifest: Manifest
    sandbox: SandboxRunner


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def check_on_base(config: DifferentialConfig, files: list[str]) -> dict[str, str]:
    results = dict.fromkeys(files, NOT_APPLICABLE)
    if not files:
        return results

    temporary = Path(tempfile.mkdtemp(prefix="taskly-base-"))
    worktree = temporary / "tree"
    added = _git(
        ["worktree", "add", "--detach", str(worktree), config.base_sha], config.trusted_dir
    )
    if added.returncode != 0:
        return results

    try:
        for path in files:
            stack = stack_of(path)
            if stack is None:
                results[path] = NOT_APPLICABLE
                continue
            decision = next(
                (item for item in config.manifest.decisions if item.target_test_file == path),
                None,
            )
            source = decision.file if decision is not None else None
            if source is None or not (worktree / source).is_file():
                results[path] = NOT_APPLICABLE
                continue

            destination = worktree / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(config.pr_dir / path, destination)

            relative = path[len(stack) + 1 :]
            run = config.sandbox.run(stack, [relative], repo=worktree)
            results[path] = PASSED_ON_BASE if run.succeeded else FAILED_ON_BASE
    finally:
        _git(["worktree", "remove", "--force", str(worktree)], config.trusted_dir)
        shutil.rmtree(temporary, ignore_errors=True)

    return results


def stack_of(path: str) -> Stack | None:
    head = path.split("/", 1)[0]
    return cast(Stack, head) if head in ("backend", "frontend") else None
