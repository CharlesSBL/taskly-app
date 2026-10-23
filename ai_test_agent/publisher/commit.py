"""Fail-closed application of the verified patch.

This is the only code path that writes to a branch. It re-verifies the patch
hash, re-checks the path allowlist, and refuses to touch anything except test
files, even though the verifier already did those checks.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .runner import Runner

BACKEND_TEST = re.compile(r"^backend/tests/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py$")
FRONTEND_TEST = re.compile(
    r"^frontend/src/(?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+\.test\.(?:ts|tsx)$"
)
DIFF_HEADER = re.compile(r"^diff --git a/(?P<source>.+?) b/(?P<target>.+)$")
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"


@dataclass(frozen=True)
class Outcome:
    ok: bool
    message: str


def patch_sha256(patch: str) -> str:
    return hashlib.sha256(patch.encode("utf-8")).hexdigest()


def patch_paths(patch: str) -> list[str]:
    paths: list[str] = []
    for line in patch.splitlines():
        match = DIFF_HEADER.match(line)
        if match:
            paths.append(match.group("target"))
    return paths


def is_allowed_path(path: str) -> bool:
    if path.startswith("/") or "\\" in path or ".." in path.split("/"):
        return False
    if path.startswith(("ai_test_agent/", ".github/", ".claude/", "sandbox/")):
        return False
    return bool(BACKEND_TEST.fullmatch(path) or FRONTEND_TEST.fullmatch(path))


def _numstat_paths(runner: Runner, repo: Path, patch_path: Path) -> list[str] | None:
    result = runner.run(["git", "-C", str(repo), "apply", "--numstat", str(patch_path)])
    if not result.succeeded:
        return None
    paths: list[str] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            paths.append(parts[2])
        elif parts and parts[0] == "-":
            return None
    return paths


def apply_verified_patch(
    runner: Runner,
    *,
    repo: Path,
    patch_path: Path,
    expected_sha: str,
    branch: str,
    message: str,
) -> Outcome:
    if not patch_path.is_file():
        return Outcome(False, f"patch not found: {patch_path}")
    patch = patch_path.read_text(encoding="utf-8")
    if not patch.strip():
        return Outcome(False, "refusing to commit an empty patch")
    actual_sha = patch_sha256(patch)
    if actual_sha != expected_sha:
        return Outcome(
            False,
            f"patch sha256 mismatch: expected {expected_sha}, got {actual_sha}",
        )

    paths = patch_paths(patch)
    if not paths:
        return Outcome(False, "patch contains no files")
    invalid = [path for path in paths if not is_allowed_path(path)]
    if invalid:
        return Outcome(False, f"patch touches forbidden paths: {invalid}")

    numstat = _numstat_paths(runner, repo, patch_path)
    if numstat is None:
        return Outcome(False, "git apply --numstat rejected the patch")
    if sorted(numstat) != sorted(paths):
        return Outcome(False, f"numstat paths {numstat} do not match patch paths {paths}")

    check = runner.run(
        ["git", "-C", str(repo), "apply", "--check", "--whitespace=nowarn", str(patch_path)]
    )
    if not check.succeeded:
        return Outcome(False, f"patch does not apply: {check.stderr.strip()[:500]}")

    applied = runner.run(["git", "-C", str(repo), "apply", "--whitespace=nowarn", str(patch_path)])
    if not applied.succeeded:
        return Outcome(False, f"git apply failed: {applied.stderr.strip()[:500]}")

    added = runner.run(["git", "-C", str(repo), "add", "--", *paths])
    if not added.succeeded:
        return Outcome(False, f"git add failed: {added.stderr.strip()[:500]}")

    committed = runner.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            f"user.name={BOT_NAME}",
            "-c",
            f"user.email={BOT_EMAIL}",
            "commit",
            "-m",
            message,
        ]
    )
    if not committed.succeeded:
        return Outcome(False, f"git commit failed: {committed.stderr.strip()[:500]}")

    pushed = runner.run(["git", "-C", str(repo), "push", "origin", f"HEAD:refs/heads/{branch}"])
    if not pushed.succeeded:
        return Outcome(False, f"git push failed: {pushed.stderr.strip()[:500]}")

    return Outcome(True, f"committed {len(paths)} test file(s) to {branch}")
