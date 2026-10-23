from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

import pytest

from agent.manifest import Decision, Manifest
from verifier.cli import main, run
from verifier.patch_builder import patch_sha256
from verifier.sandbox import CommandResult

BACKEND_PATH = "backend/tests/test_feature.py"
BACKEND_SOURCE = "def test_add():\n    assert 1 + 1 == 2\n"


class FakeSandbox:
    def __init__(self, report_dir: Path, *, success: bool = True) -> None:
        self.report_dir = report_dir
        self.success = success
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        stack: str,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
        repo: Path | None = None,
    ) -> CommandResult:
        self.calls.append({"stack": stack, "coverage": coverage, "repo": repo})
        if coverage:
            (self.report_dir / "be_coverage.json").write_text(
                json.dumps({"totals": {"percent_covered": 55.0}})
            )
        return CommandResult(0 if self.success else 1, "1 passed" if self.success else "1 failed")


def block(path: str, source: str) -> str:
    added = "".join(f"+{line}\n" for line in source.splitlines())
    return (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n"
        f"+++ b/{path}\n@@ -0,0 +1,{len(source.splitlines())} @@\n{added}"
    )


def make_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "pr"
    (repo / "backend/tests").mkdir(parents=True)
    (repo / "backend/tests/__init__.py").write_text("")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def manifest(target: str = BACKEND_PATH) -> Manifest:
    return Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        decisions=[
            Decision(
                file="backend/app/feature.py",
                action="create",
                rationale="new logic",
                target_test_file=target,
            )
        ],
        files_written=[target],
    )


def write_inputs(tmp_path: Path, patch: str, manifest_obj: Manifest) -> tuple[Path, Path, Path]:
    manifest_path = tmp_path / "agent_manifest.json"
    manifest_path.write_text(manifest_obj.to_json())
    patch_path = tmp_path / "candidate_tests.patch"
    patch_path.write_text(patch)
    return manifest_path, patch_path, tmp_path / "out"


def test_happy_path_applies_patch_and_writes_report(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest_path, patch_path, out = write_inputs(tmp_path, patch, manifest(BACKEND_PATH))
    sandbox = FakeSandbox(out)

    report, code = run(
        pr_dir=repo,
        trusted_dir=repo,
        base_sha="",
        manifest_path=manifest_path,
        patch_path=patch_path,
        out_dir=out,
        sandbox=sandbox,
    )

    assert code == 0
    assert report.status == "passed", report.notes
    assert report.accepted_stacks == ["backend"]
    assert (repo / BACKEND_PATH).is_file()
    assert (out / "verified_tests.patch").read_text() == patch
    raw = json.loads((out / "verification_report.json").read_text())
    assert raw["status"] == "passed"
    assert raw["patch_sha256"] == patch_sha256(patch)


def test_integrity_violation_exits_one_without_applying(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    bad = block(".github/workflows/test_x.py", "def test_x(): pass\n")
    manifest_path, patch_path, out = write_inputs(
        tmp_path, bad, manifest(".github/workflows/test_x.py")
    )

    report, code = run(
        pr_dir=repo,
        trusted_dir=repo,
        base_sha="",
        manifest_path=manifest_path,
        patch_path=patch_path,
        out_dir=out,
        sandbox=FakeSandbox(out),
    )

    assert code == 1
    assert report.status == "rejected"
    assert any("tooling" in violation for violation in report.notes)
    assert not (repo / ".github").exists()
    assert (out / "verified_tests.patch").read_text() == ""


def test_invalid_manifest_is_rejected(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    manifest_path = tmp_path / "agent_manifest.json"
    manifest_path.write_text("{}")
    patch_path = tmp_path / "candidate_tests.patch"
    patch_path.write_text("")
    out = tmp_path / "out"

    report, code = run(
        pr_dir=repo,
        trusted_dir=repo,
        base_sha="",
        manifest_path=manifest_path,
        patch_path=patch_path,
        out_dir=out,
        sandbox=FakeSandbox(out),
    )

    assert code == 1
    assert report.status == "rejected"
    assert "invalid manifest" in report.notes[0]


def test_patch_that_does_not_apply_is_rejected(tmp_path: Path) -> None:
    repo = make_git_repo(tmp_path)
    (repo / "backend/tests/__init__.py").write_text("existing\n")
    path = "backend/tests/__init__.py"
    patch = (
        f"diff --git a/{path} b/{path}\n"
        "index 1111111..2222222 100644\n"
        f"--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-wrong context\n+new\n"
    )
    manifest_obj = Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        files_written=[path],
    )
    manifest_path, patch_path, out = write_inputs(tmp_path, patch, manifest_obj)

    report, code = run(
        pr_dir=repo,
        trusted_dir=repo,
        base_sha="",
        manifest_path=manifest_path,
        patch_path=patch_path,
        out_dir=out,
        sandbox=FakeSandbox(out),
    )

    assert code == 1
    assert report.status == "rejected"
    assert "does not apply" in report.notes[0]


def test_main_returns_one_for_rejection(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = make_git_repo(tmp_path)
    bad = block(".github/workflows/test_x.py", "def test_x(): pass\n")
    manifest_path, patch_path, out = write_inputs(
        tmp_path, bad, manifest(".github/workflows/test_x.py")
    )

    exit_code = main(
        [
            "--pr-dir",
            str(repo),
            "--trusted-dir",
            str(repo),
            "--manifest",
            str(manifest_path),
            "--patch",
            str(patch_path),
            "--out",
            str(out),
            "--skip-differential",
        ],
        sandbox=FakeSandbox(out),
    )

    assert exit_code == 1
    assert "tooling" in capsys.readouterr().err
