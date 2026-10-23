"""Build the candidate test patch from the files the agent wrote."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


def build_candidate_patch(repo_root: Path, files: Sequence[str], destination: Path) -> Path:
    """Return a `git diff` patch for new or modified test files.

    New files are marked intent-to-add so they appear in the diff without being
    committed.
    """
    if not files:
        destination.write_text("", encoding="utf-8")
        return destination

    subprocess.run(
        ["git", "-C", str(repo_root), "add", "--intent-to-add", "--", *files],
        check=True,
        capture_output=True,
        text=True,
    )
    diff = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--no-color", "--", *files],
        check=True,
        capture_output=True,
        text=True,
    )
    destination.write_text(diff.stdout, encoding="utf-8")
    return destination
