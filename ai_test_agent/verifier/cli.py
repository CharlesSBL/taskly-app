"""`python -m verifier --verify-only ...`

Runs the full gate on the untrusted agent artifact. Exit code 1 means the
artifact was rejected (integrity failure or a patch that does not apply);
reverted stacks are a normal, reported outcome with exit code 0.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from pydantic import ValidationError

from agent.manifest import Manifest, load_manifest

from .differential import DifferentialConfig, check_on_base
from .gate import GateConfig, verify
from .integrity import check_patch
from .patch_builder import patch_sha256, split_patch
from .sandbox import SandboxRunner, SubprocessSandbox
from .types import VerificationReport

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m verifier")
    parser.add_argument("--verify-only", action="store_true", help="run the gate only")
    parser.add_argument("--pr-dir", type=Path, required=True)
    parser.add_argument("--trusted-dir", type=Path, required=True)
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sandbox-script", type=Path)
    parser.add_argument("--skip-differential", action="store_true")
    return parser


def _apply_patch(pr_dir: Path, patch_path: Path) -> str | None:
    """Return an error string when the patch cannot be applied."""
    check = subprocess.run(
        ["git", "-C", str(pr_dir), "apply", "--check", "--whitespace=nowarn", str(patch_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if check.returncode != 0:
        return (check.stdout + check.stderr).strip()[:1000]
    applied = subprocess.run(
        ["git", "-C", str(pr_dir), "apply", "--whitespace=nowarn", str(patch_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if applied.returncode != 0:
        return (applied.stdout + applied.stderr).strip()[:1000]
    return None


def _rejected(out_dir: Path, violations: list[str]) -> VerificationReport:
    report = VerificationReport(
        status="rejected",
        accepted_stacks=[],
        reverted_stacks={},
        coverage={},
        differential={},
        patch_sha256=patch_sha256(""),
        notes=violations,
        verified_patch="",
    )
    _write_outputs(out_dir, report)
    return report


def _write_outputs(out_dir: Path, report: VerificationReport) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "verified_tests.patch").write_text(report.verified_patch, encoding="utf-8")
    (out_dir / "verification_report.json").write_text(
        json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8"
    )


def run(
    *,
    pr_dir: Path,
    trusted_dir: Path,
    base_sha: str,
    manifest_path: Path,
    patch_path: Path,
    out_dir: Path,
    sandbox: SandboxRunner,
    skip_differential: bool = False,
) -> tuple[VerificationReport, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        manifest: Manifest = load_manifest(manifest_path)
    except (OSError, ValidationError) as exc:
        report = _rejected(out_dir, [f"invalid manifest: {exc}"])
        return report, 1

    patch = patch_path.read_text(encoding="utf-8") if patch_path.is_file() else ""
    integrity = check_patch(patch, manifest)
    if not integrity.ok:
        return _rejected(out_dir, integrity.violations), 1

    if patch and integrity.paths:
        apply_error = _apply_patch(pr_dir, patch_path)
        if apply_error:
            return _rejected(out_dir, [f"patch does not apply: {apply_error}"]), 1

    report = verify(
        GateConfig(
            pr_dir=pr_dir,
            manifest=manifest,
            patch=patch,
            sandbox=sandbox,
            report_dir=out_dir,
        )
    )

    if report.accepted_stacks and base_sha and not skip_differential:
        accepted_paths = [
            path for path in integrity.paths if path.split("/", 1)[0] in report.accepted_stacks
        ]
        report.differential = check_on_base(
            DifferentialConfig(
                trusted_dir=trusted_dir,
                base_sha=base_sha,
                pr_dir=pr_dir,
                manifest=manifest,
                sandbox=sandbox,
            ),
            accepted_paths,
        )

    (out_dir / "verified_tests.patch").write_text(report.verified_patch, encoding="utf-8")
    (out_dir / "verification_report.json").write_text(
        json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report, 0


def main(argv: list[str] | None = None, *, sandbox: SandboxRunner | None = None) -> int:
    args = build_parser().parse_args(argv)
    runner = sandbox or SubprocessSandbox(
        script=args.sandbox_script or (PACKAGE_ROOT / "sandbox" / "run.sh"),
        out_dir=args.out.resolve(),
    )
    report, code = run(
        pr_dir=args.pr_dir.resolve(),
        trusted_dir=args.trusted_dir.resolve(),
        base_sha=args.base_sha,
        manifest_path=args.manifest.resolve(),
        patch_path=args.patch.resolve(),
        out_dir=args.out.resolve(),
        sandbox=runner,
        skip_differential=args.skip_differential,
    )
    print(
        json.dumps(
            {
                "gate_status": report.status,
                "accepted_stacks": ",".join(report.accepted_stacks),
                "patch_sha256": report.patch_sha256,
                "reverted_stacks": ",".join(sorted(report.reverted_stacks)),
                "files": len(split_patch(report.verified_patch)),
            },
            indent=2,
        )
    )
    if code == 0:
        return 0
    print("\n".join(report.notes), file=sys.stderr)
    return code
