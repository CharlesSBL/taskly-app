from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from agent.manifest import Decision, Manifest
from publisher.cli import load_report, main
from publisher.comment import MARKER
from publisher.commit import patch_sha256
from publisher.runner import RunResult
from verifier.types import VerificationReport


class ScriptedRunner:
    def __init__(self, responses: dict[str, RunResult] | None = None) -> None:
        self.responses = responses or {}
        self.calls: list[list[str]] = []

    def run(self, args: Sequence[str], cwd: Path | None = None) -> RunResult:
        self.calls.append(list(args))
        joined = " ".join(args)
        for needle, result in self.responses.items():
            if needle in joined:
                return result
        return RunResult(0, "")


def make_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    manifest = Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        decisions=[
            Decision(file="backend/app/x.py", action="skip", rationale="docs"),
        ],
    )
    manifest_path = tmp_path / "agent_manifest.json"
    manifest_path.write_text(manifest.to_json())

    report = VerificationReport(
        status="nothing_to_test",
        accepted_stacks=[],
        reverted_stacks={},
        coverage={},
        differential={},
        patch_sha256="",
    )
    report_path = tmp_path / "verification_report.json"
    report_path.write_text(json.dumps(report.as_dict()))

    return manifest_path, report_path, tmp_path / "comment.md"


def test_comment_command_writes_markdown(tmp_path: Path) -> None:
    manifest_path, report_path, out = make_inputs(tmp_path)
    code = main(
        [
            "comment",
            "--manifest",
            str(manifest_path),
            "--report",
            str(report_path),
            "--out",
            str(out),
        ],
        runner=ScriptedRunner(),
    )
    assert code == 0
    assert out.read_text().startswith(MARKER)
    assert "Nothing to test" in out.read_text()


def test_authorize_command_denies_read_permission(tmp_path: Path) -> None:
    runner = ScriptedRunner({"collaborators/": RunResult(0, '{"permission": "read"}')})
    code = main(["authorize", "--repo", "o/r", "--login", "alice"], runner=runner)
    assert code == 1


def test_authorize_command_allows_admin(tmp_path: Path) -> None:
    runner = ScriptedRunner({"collaborators/": RunResult(0, '{"permission": "admin"}')})
    assert main(["authorize", "--repo", "o/r", "--login", "alice"], runner=runner) == 0


def test_commit_command(tmp_path: Path) -> None:
    path = "backend/tests/test_feature.py"
    patch = (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n"
        f"+++ b/{path}\n@@ -0,0 +1 @@\n+def test_x():\n+    assert 1 == 1\n"
    )
    patch_path = tmp_path / "verified_tests.patch"
    patch_path.write_text(patch)
    runner = ScriptedRunner({"apply --numstat": RunResult(0, f"1\t0\t{path}\n")})

    code = main(
        [
            "commit",
            "--repo-dir",
            str(tmp_path),
            "--patch",
            str(patch_path),
            "--sha",
            patch_sha256(patch),
            "--branch",
            "ai-tests/x",
            "--message",
            "test: add",
        ],
        runner=runner,
    )
    assert code == 0
    assert any("push origin HEAD:refs/heads/ai-tests/x" in " ".join(call) for call in runner.calls)


def test_commit_command_fails_on_sha_mismatch(tmp_path: Path) -> None:
    patch_path = tmp_path / "p.patch"
    patch_path.write_text("diff --git a/backend/tests/test_x.py b/backend/tests/test_x.py\n")
    code = main(
        [
            "commit",
            "--repo-dir",
            str(tmp_path),
            "--patch",
            str(patch_path),
            "--sha",
            "0" * 64,
            "--branch",
            "ai-tests/x",
            "--message",
            "test: add",
        ],
        runner=ScriptedRunner(),
    )
    assert code == 1


def test_load_report_rejects_unknown_shape(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps(
            {
                "status": "passed",
                "accepted_stacks": ["backend"],
                "patch_sha256": "x",
            }
        )
    )
    report = load_report(path)
    assert report.status == "passed"
    assert report.reverted_stacks == {}
