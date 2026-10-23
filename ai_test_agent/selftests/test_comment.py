from __future__ import annotations

from agent.manifest import Baseline, Decision, Manifest
from publisher.comment import MARKER, render_comment
from verifier.types import GateStatus, VerificationReport


def manifest(lockfile_changed: bool = False) -> Manifest:
    return Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        decisions=[
            Decision(
                file="backend/app/core/config.py",
                action="create",
                rationale="config has no tests | at all",
                skill_used="backend-pytest-conventions",
                target_test_file="backend/tests/core/test_config.py",
                test_claims=["explicit URL wins", "missing variables raise KeyError"],
            ),
            Decision(
                file="frontend/src/lib/http.ts",
                action="update",
                rationale="error branch is untested",
                skill_used="frontend-vitest-conventions",
                target_test_file="frontend/src/lib/http.test.ts",
                test_claims=["422 produces a validation message"],
            ),
            Decision(file="README.md", action="skip", rationale="documentation"),
        ],
        files_written=["backend/tests/core/test_config.py", "frontend/src/lib/http.test.ts"],
        skills_used=["analyze-diff", "backend-pytest-conventions"],
        turns=7,
        input_tokens=12_345,
        output_tokens=2_000,
        cost_usd=0.0446,
        lockfile_changed=lockfile_changed,
        baseline={"backend": Baseline(status="passed", tests=21, coverage=42.0)},
    )


def report(status: GateStatus = "passed") -> VerificationReport:
    return VerificationReport(
        status=status,
        accepted_stacks=["backend"],
        reverted_stacks={} if status == "passed" else {"frontend": ["tests failed: 1 failed"]},
        coverage={
            "backend": {
                "before": 42.0,
                "after": 49.7,
                "delta": 7.7,
                "tests": 3,
                "flaky": False,
            }
        },
        differential={
            "backend/tests/core/test_config.py": "true",
            "backend/tests/core/test_other.py": "false",
            "backend/tests/core/test_new.py": "n/a",
        },
        patch_sha256="a" * 64,
        notes=[],
        verified_patch=(
            "diff --git a/backend/tests/core/test_config.py b/backend/tests/core/test_config.py\n"
        ),
    )


def test_comment_starts_with_the_marker_and_has_the_core_sections() -> None:
    comment = render_comment(manifest(), report(), trace_url="https://trace", run_url="https://run")
    assert comment.startswith(MARKER)
    assert "✅ Tests verified" in comment
    assert "### Decisions" in comment
    assert "### Coverage" in comment
    assert "### Differential" in comment
    assert "### What the tests claim to verify" in comment
    assert "`backend/tests/core/test_config.py`" in comment
    assert "➕ create" in comment
    assert "♻️ update" in comment
    assert "⏭️ skip" in comment
    assert "explicit URL wins" in comment
    assert "42.00%" in comment
    assert "49.70%" in comment
    assert "+7.70%" in comment
    assert "Failed on base / passed on PR" in comment
    assert "Passed on both" in comment
    assert "https://trace" in comment
    assert "https://run" in comment


def test_table_cells_escape_pipes() -> None:
    comment = render_comment(manifest(), report())
    assert "config has no tests \\| at all" in comment


def test_patch_is_in_a_collapsible_block_with_the_hash() -> None:
    comment = render_comment(manifest(), report())
    assert "<details><summary>📋 Verified test patch (git apply)</summary>" in comment
    assert "````diff" in comment
    assert "a" * 64 in comment
    assert "ai-tests:commit" in comment


def test_lockfile_warning() -> None:
    comment = render_comment(manifest(lockfile_changed=True), report())
    assert "Lockfiles changed" in comment


def test_reverted_warning_and_state() -> None:
    comment = render_comment(manifest(), report("reverted"))
    assert "⚠️ Tests reverted" in comment
    assert "tests failed: 1 failed" in comment
    assert "frontend" in comment


def test_rejected_and_empty_states() -> None:
    rejected_report = report("rejected")
    rejected_report.verified_patch = ""
    rejected = render_comment(manifest(), rejected_report)
    assert "🛑 Output rejected" in rejected
    assert "failed integrity checks" in rejected
    assert "_No patch was accepted._" in rejected

    nothing = render_comment(manifest(), report("nothing_to_test"))
    assert "⏭️ Nothing to test" in nothing


def test_budget_exceeded_is_flagged() -> None:
    manifest_obj = manifest()
    manifest_obj.status = "budget_exceeded"
    comment = render_comment(manifest_obj, report())
    assert "budget_exceeded" in comment


def test_agent_error_state() -> None:
    manifest_obj = manifest()
    manifest_obj.status = "error"
    comment = render_comment(manifest_obj, report())
    assert "❌ Agent error" in comment


def test_empty_differential_is_explained() -> None:
    report_obj = report()
    report_obj.differential = {}
    assert "Differential check did not run" in render_comment(manifest(), report_obj)


def test_no_decisions_and_no_claims_are_handled() -> None:
    manifest_obj = manifest()
    manifest_obj.decisions = []
    comment = render_comment(manifest_obj, report())
    assert "_No decisions were recorded._" in comment
    assert "_No behavior claims were made._" in comment
