from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from agent.manifest import Baseline, Decision, Manifest, Stack
from verifier.gate import GateConfig, verify
from verifier.patch_builder import patch_sha256
from verifier.sandbox import CommandResult

BACKEND_PATH = "backend/tests/test_feature.py"
FRONTEND_PATH = "frontend/src/features/Foo.test.tsx"
BACKEND_SOURCE = "def test_add():\n    assert 1 + 1 == 2\n"
FRONTEND_SOURCE = "it('renders', () => { expect(screen.getByText('x')).toBeVisible() })\n"


def block(path: str, source: str) -> str:
    added = "".join(f"+{line}\n" for line in source.splitlines())
    return (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n"
        f"+++ b/{path}\n@@ -0,0 +1,{len(source.splitlines())} @@\n{added}"
    )


Handler = Callable[..., CommandResult]


class FakeSandbox:
    def __init__(
        self,
        report_dir: Path,
        *,
        coverage: dict[str, float] | None = None,
        handler: Handler | None = None,
    ) -> None:
        self.report_dir = report_dir
        self.coverage = coverage or {}
        self.handler = handler or (lambda **_: CommandResult(0, "5 passed in 0.1s"))
        self.calls: list[dict[str, Any]] = []

    def run(
        self,
        stack: str,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
        repo: Path | None = None,
    ) -> CommandResult:
        self.calls.append(
            {
                "stack": stack,
                "paths": list(paths),
                "coverage": coverage,
                "typecheck": typecheck,
                "repo": repo,
            }
        )
        if coverage and stack in self.coverage:
            if stack == "backend":
                (self.report_dir / "be_coverage.json").write_text(
                    json.dumps({"totals": {"percent_covered": self.coverage[stack]}})
                )
            else:
                directory = self.report_dir / "fe_coverage"
                directory.mkdir(exist_ok=True)
                (directory / "coverage-summary.json").write_text(
                    json.dumps({"total": {"lines": {"pct": self.coverage[stack]}}})
                )
        return self.handler(stack=stack, coverage=coverage, typecheck=typecheck, paths=paths)


def make_pr(tmp_path: Path, files: dict[str, str]) -> Path:
    pr = tmp_path / "pr"
    for path, source in files.items():
        target = pr / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source)
    return pr


def make_manifest(targets: list[str], baseline: dict[Stack, Baseline] | None = None) -> Manifest:
    decisions = [
        Decision(
            file=target.replace("/tests/", "/app/").replace(".test.tsx", ".tsx"),
            action="create",
            rationale="new logic",
            target_test_file=target,
        )
        for target in targets
    ]
    return Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        decisions=decisions,
        files_written=targets,
        baseline=baseline or {},
    )


def config(tmp_path: Path, manifest: Manifest, patch: str, sandbox: FakeSandbox) -> GateConfig:
    return GateConfig(
        pr_dir=tmp_path / "pr",
        manifest=manifest,
        patch=patch,
        sandbox=sandbox,
        report_dir=tmp_path / "out",
        lint=lambda _pr, _files: CommandResult(0, ""),
    )


def test_accepted_stack_reports_coverage_delta(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH], {"backend": Baseline(status="passed", coverage=42.0)})
    (tmp_path / "out").mkdir()
    sandbox = FakeSandbox(tmp_path / "out", coverage={"backend": 55.5})

    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "passed"
    assert report.accepted_stacks == ["backend"]
    assert report.reverted_stacks == {}
    assert report.coverage["backend"]["before"] == 42.0
    assert report.coverage["backend"]["after"] == 55.5
    assert report.coverage["backend"]["delta"] == 13.5
    assert report.patch_sha256 == patch_sha256(patch)
    assert report.verified_patch == patch
    assert report.notes == []


def test_test_failure_reverts_only_that_stack(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH])
    (tmp_path / "out").mkdir()
    sandbox = FakeSandbox(
        tmp_path / "out",
        handler=lambda **kw: (
            CommandResult(0, "1 passed") if kw["coverage"] else CommandResult(1, "1 failed in 0.1s")
        ),
    )

    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "reverted"
    assert report.accepted_stacks == []
    assert "1 failed" in report.reverted_stacks["backend"][0]
    assert report.verified_patch == ""


def test_flaky_second_run_is_rejected(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH])
    (tmp_path / "out").mkdir()
    runs = {"count": 0}

    def handler(**kwargs: Any) -> CommandResult:
        if kwargs["coverage"]:
            return CommandResult(0, "")
        runs["count"] += 1
        return CommandResult(0 if runs["count"] == 1 else 1, "passed then failed")

    sandbox = FakeSandbox(tmp_path / "out", handler=handler)
    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "reverted"
    assert report.coverage["backend"]["flaky"] is True
    assert "flaky" in report.reverted_stacks["backend"][0]


def test_lint_failure_reverts(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH])
    (tmp_path / "out").mkdir()
    gate_config = config(tmp_path, manifest, patch, FakeSandbox(tmp_path / "out"))
    gate_config.lint = lambda _pr, _files: CommandResult(1, "E501 line too long")

    report = verify(gate_config)

    assert report.status == "reverted"
    assert "ruff" in report.reverted_stacks["backend"][0]


def test_frontend_typecheck_failure_reverts(tmp_path: Path) -> None:
    make_pr(tmp_path, {FRONTEND_PATH: FRONTEND_SOURCE})
    patch = block(FRONTEND_PATH, FRONTEND_SOURCE)
    manifest = make_manifest([FRONTEND_PATH])
    (tmp_path / "out").mkdir()
    sandbox = FakeSandbox(
        tmp_path / "out",
        handler=lambda **kw: (
            CommandResult(1, "TS2304: Cannot find name")
            if kw["typecheck"]
            else CommandResult(0, "")
        ),
    )

    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "reverted"
    assert "tsc" in report.reverted_stacks["frontend"][0]
    typecheck_calls = [call for call in sandbox.calls if call["typecheck"]]
    assert typecheck_calls[0]["paths"] == ["src/features/Foo.test.tsx"]


def test_failing_full_suite_reverts_the_stack(tmp_path: Path) -> None:
    """The coverage run executes the whole suite, so a red suite must revert."""
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH])
    (tmp_path / "out").mkdir()
    sandbox = FakeSandbox(
        tmp_path / "out",
        handler=lambda **kw: (
            CommandResult(1, "2 failed, 39 passed")
            if kw["coverage"]
            else CommandResult(0, "5 passed")
        ),
    )

    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "reverted"
    assert "full suite failed" in report.reverted_stacks["backend"][0]


def test_unfulfilled_create_is_rejected(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest(["backend/tests/test_missing.py"])
    manifest.files_written = [BACKEND_PATH]
    (tmp_path / "out").mkdir()

    report = verify(config(tmp_path, manifest, patch, FakeSandbox(tmp_path / "out")))

    assert report.status == "reverted"
    assert "unfulfilled" in report.reverted_stacks["backend"][0]


def test_baseline_failure_skips_the_stack(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH], {"backend": Baseline(status="failed")})
    (tmp_path / "out").mkdir()

    report = verify(config(tmp_path, manifest, patch, FakeSandbox(tmp_path / "out")))

    assert report.status == "baseline_failing"
    assert "baseline failing" in report.reverted_stacks["backend"][0]


def test_nothing_to_test_when_only_skips(tmp_path: Path) -> None:
    manifest = Manifest(
        status="nothing_to_test",
        model="claude-sonnet-5-5",
        decisions=[Decision(file="README.md", action="skip", rationale="docs")],
    )
    report = verify(config(tmp_path, manifest, "", FakeSandbox(tmp_path / "out")))
    assert report.status == "nothing_to_test"
    assert report.accepted_stacks == []


def test_one_good_stack_survives_a_bad_one(tmp_path: Path) -> None:
    make_pr(tmp_path, {BACKEND_PATH: BACKEND_SOURCE, FRONTEND_PATH: FRONTEND_SOURCE})
    patch = block(BACKEND_PATH, BACKEND_SOURCE) + block(FRONTEND_PATH, FRONTEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH, FRONTEND_PATH])
    (tmp_path / "out").mkdir()
    sandbox = FakeSandbox(
        tmp_path / "out",
        coverage={"backend": 60.0, "frontend": 50.0},
        handler=lambda **kw: (
            CommandResult(1, "suite failed")
            if kw["stack"] == "frontend" and not kw["typecheck"] and not kw["coverage"]
            else CommandResult(0, "1 passed")
        ),
    )

    report = verify(config(tmp_path, manifest, patch, sandbox))

    assert report.status == "passed"
    assert report.accepted_stacks == ["backend"]
    assert "frontend" in report.reverted_stacks
    assert BACKEND_PATH in report.verified_patch
    assert FRONTEND_PATH not in report.verified_patch


def test_declared_file_missing_after_apply_is_rejected(tmp_path: Path) -> None:
    make_pr(tmp_path, {})
    patch = block(BACKEND_PATH, BACKEND_SOURCE)
    manifest = make_manifest([BACKEND_PATH])
    (tmp_path / "out").mkdir()
    report = verify(config(tmp_path, manifest, patch, FakeSandbox(tmp_path / "out")))
    assert report.status == "reverted"
    assert "missing after apply" in report.reverted_stacks["backend"][0]
