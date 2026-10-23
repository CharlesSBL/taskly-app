"""Open or update the coverage-backfill pull request.

Never pushes to the default branch: the branch name is validated and the PR is
always created against `main`.
"""

from __future__ import annotations

from pathlib import Path

from .commit import Outcome
from .runner import Runner

PROTECTED_BRANCHES = {"main", "master"}


def open_backfill_pr(
    runner: Runner,
    *,
    repo: str,
    branch: str,
    base_branch: str,
    title: str,
    body_path: Path,
    repo_dir: Path,
) -> Outcome:
    if branch in PROTECTED_BRANCHES or branch == base_branch:
        return Outcome(False, f"refusing to open a PR from protected branch {branch!r}")
    if not body_path.is_file():
        return Outcome(False, f"PR body not found: {body_path}")

    pushed = runner.run(
        ["git", "-C", str(repo_dir), "push", "-u", "origin", f"HEAD:refs/heads/{branch}"]
    )
    if not pushed.succeeded:
        return Outcome(False, f"git push failed: {pushed.stderr.strip()[:500]}")

    existing = runner.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--head",
            branch,
            "--state",
            "open",
            "--json",
            "number",
            "--jq",
            ".[0].number",
        ]
    )
    number = existing.stdout.strip() if existing.succeeded else ""
    if number.isdigit():
        updated = runner.run(
            [
                "gh",
                "pr",
                "edit",
                number,
                "--repo",
                repo,
                "--title",
                title,
                "--body-file",
                str(body_path),
            ]
        )
        if not updated.succeeded:
            return Outcome(False, f"gh pr edit failed: {updated.stderr.strip()[:500]}")
        return Outcome(True, f"updated PR #{number} from {branch}")

    created = runner.run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            repo,
            "--base",
            base_branch,
            "--head",
            branch,
            "--title",
            title,
            "--body-file",
            str(body_path),
        ]
    )
    if not created.succeeded:
        return Outcome(False, f"gh pr create failed: {created.stderr.strip()[:500]}")
    return Outcome(True, f"opened PR from {branch}: {created.stdout.strip()}")
