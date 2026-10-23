"""Publisher CLI: render the comment, authorize a labeler, commit, or open the backfill PR."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from agent.manifest import load_manifest
from verifier.types import GateStatus, VerificationReport

from .authorize import AuthorizationError, authorize, labeler_permission
from .backfill import open_backfill_pr
from .comment import render_comment
from .commit import apply_verified_patch
from .runner import Runner, SubprocessRunner


def load_report(path: Path) -> VerificationReport:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return VerificationReport(
        status=cast(GateStatus, raw["status"]),
        accepted_stacks=list(raw.get("accepted_stacks", [])),
        reverted_stacks={key: list(value) for key, value in raw.get("reverted_stacks", {}).items()},
        coverage=dict(raw.get("coverage", {})),
        differential=dict(raw.get("differential", {})),
        patch_sha256=str(raw.get("patch_sha256", "")),
        notes=list(raw.get("notes", [])),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m publisher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    comment = subparsers.add_parser("comment", help="render the sticky PR comment")
    comment.add_argument("--manifest", type=Path, required=True)
    comment.add_argument("--report", type=Path, required=True)
    comment.add_argument("--out", type=Path, required=True)
    comment.add_argument("--trace-url")
    comment.add_argument("--run-url")

    authorize_parser = subparsers.add_parser("authorize", help="check labeler permission")
    authorize_parser.add_argument("--repo", required=True)
    authorize_parser.add_argument("--login", required=True)

    commit = subparsers.add_parser("commit", help="apply the verified patch")
    commit.add_argument("--repo-dir", type=Path, required=True)
    commit.add_argument("--patch", type=Path, required=True)
    commit.add_argument("--sha", required=True)
    commit.add_argument("--branch", required=True)
    commit.add_argument("--message", required=True)
    commit.add_argument("--force", action="store_true")

    backfill = subparsers.add_parser("backfill", help="open or update the backfill PR")
    backfill.add_argument("--repo", required=True)
    backfill.add_argument("--repo-dir", type=Path, required=True)
    backfill.add_argument("--branch", required=True)
    backfill.add_argument("--base-branch", default="main")
    backfill.add_argument("--title", required=True)
    backfill.add_argument("--body", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None, *, runner: Runner | None = None) -> int:
    args = build_parser().parse_args(argv)
    active = runner or SubprocessRunner()

    if args.command == "comment":
        manifest = load_manifest(args.manifest)
        report = load_report(args.report)
        comment = render_comment(manifest, report, trace_url=args.trace_url, run_url=args.run_url)
        args.out.write_text(comment + "\n", encoding="utf-8")
        print(args.out)
        return 0

    if args.command == "authorize":
        permission = labeler_permission(active, args.repo, args.login)
        try:
            authorize(active, args.repo, args.login)
        except AuthorizationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"authorized ({permission})")
        return 0

    if args.command == "commit":
        outcome = apply_verified_patch(
            active,
            repo=args.repo_dir.resolve(),
            patch_path=args.patch.resolve(),
            expected_sha=args.sha,
            branch=args.branch,
            message=args.message,
            force=args.force,
        )
        print(outcome.message, file=sys.stdout if outcome.ok else sys.stderr)
        return 0 if outcome.ok else 1

    outcome = open_backfill_pr(
        active,
        repo=args.repo,
        repo_dir=args.repo_dir.resolve(),
        branch=args.branch,
        base_branch=args.base_branch,
        title=args.title,
        body_path=args.body.resolve(),
    )
    print(outcome.message, file=sys.stdout if outcome.ok else sys.stderr)
    return 0 if outcome.ok else 1
