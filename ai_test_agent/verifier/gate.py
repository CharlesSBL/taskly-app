"""Per-stack verification gate.

A stack is reverted, not the whole run, when its tests fail a check. Every
failure is recorded with a reason and surfaced in the pull request comment.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from agent.manifest import Manifest, Stack
from lint_policy import run_ruff

from .ast_quality import check_source
from .coverage import read_coverage
from .patch_builder import build_patch, patch_sha256, split_patch
from .sandbox import CommandResult, SandboxRunner
from .types import GateStatus, StackGate, VerificationReport

STACKS: tuple[Stack, ...] = ("backend", "frontend")
TESTS_PASSED = re.compile(r"(\d+) passed")


def ruff_lint(pr_dir: Path, files: Sequence[str]) -> CommandResult:
    result = run_ruff(pr_dir, files)
    return CommandResult(returncode=result.returncode, output=result.output)


def _tail(text: str, limit: int = 300) -> str:
    return text.strip()[-limit:]


def _stack_relative(stack: Stack, path: str) -> str:
    prefix = f"{stack}/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def _tests_passed(output: str) -> int | None:
    match = TESTS_PASSED.search(output)
    return int(match.group(1)) if match else None


@dataclass
class GateConfig:
    pr_dir: Path
    manifest: Manifest
    patch: str
    sandbox: SandboxRunner
    report_dir: Path
    lint: Callable[[Path, Sequence[str]], CommandResult] | None = None
    run_flakiness: bool = True
    notes: list[str] = field(default_factory=list)


def _decision_targets(manifest: Manifest, stack: Stack) -> list[str]:
    prefix = f"{stack}/"
    return [
        decision.target_test_file
        for decision in manifest.decisions
        if decision.action != "skip"
        and decision.target_test_file is not None
        and decision.target_test_file.startswith(prefix)
    ]


def _run_stack(config: GateConfig, stack: Stack, paths: list[str]) -> StackGate:
    gate = StackGate(stack=stack)
    baseline = config.manifest.baseline.get(stack)
    gate.coverage_before = baseline.coverage if baseline is not None else None

    if baseline is not None and baseline.status == "failed":
        gate.reject("baseline failing; stack left untouched")
        return gate

    stack_files = [path for path in paths if path.startswith(f"{stack}/")]
    targets = _decision_targets(config.manifest, stack)
    if not stack_files:
        gate.reject("decisions declared but no test files were written")
        return gate

    missing = sorted(set(targets) - set(stack_files))
    if missing:
        gate.reject(f"unfulfilled create/update: {', '.join(missing)}")

    for relative in stack_files:
        path = config.pr_dir / relative
        if not path.is_file():
            gate.reject(f"declared test file is missing after apply: {relative}")
            continue
        source = path.read_text(encoding="utf-8", errors="replace")
        issues = check_source(relative, source)
        if issues:
            gate.reject("; ".join(issue.as_text() for issue in issues[:5]))

    if stack == "backend" and not gate.reasons:
        lint = config.lint or ruff_lint
        result = lint(config.pr_dir, stack_files)
        if not result.succeeded:
            gate.reject(f"ruff: {_tail(result.output)}")

    if stack == "frontend" and not gate.reasons:
        lint_paths = [_stack_relative(stack, path) for path in stack_files]
        result = config.sandbox.run(stack, lint_paths, typecheck=True, repo=config.pr_dir)
        if not result.succeeded:
            gate.reject(f"tsc/prettier: {_tail(result.output)}")

    if not gate.reasons:
        run_paths = [_stack_relative(stack, path) for path in stack_files]
        first = config.sandbox.run(stack, run_paths, repo=config.pr_dir)
        gate.tests = _tests_passed(first.output)
        if not first.succeeded:
            gate.reject(f"tests failed: {_tail(first.output)}")
        elif config.run_flakiness:
            second = config.sandbox.run(stack, run_paths, repo=config.pr_dir)
            if not second.succeeded:
                gate.flaky = True
                gate.reject("flaky: second run failed")

    if not gate.reasons:
        coverage_run = config.sandbox.run(stack, [], coverage=True, repo=config.pr_dir)
        gate.coverage_after = read_coverage(config.report_dir, stack)
        # The coverage run executes the whole suite of the stack, so a red
        # suite here means the patch broke tests the agent never ran.
        if not coverage_run.succeeded:
            gate.reject(f"full suite failed: {_tail(coverage_run.output)}")
        elif gate.coverage_after is None:
            gate.reject("no coverage report was produced")

    gate.accepted = not gate.reasons
    return gate


def verify(config: GateConfig) -> VerificationReport:
    paths = [path for path, _ in split_patch(config.patch)]
    targeted = {
        stack
        for stack in STACKS
        if _decision_targets(config.manifest, stack)
        or any(path.startswith(f"{stack}/") for path in paths)
    }

    if not paths or not targeted:
        return VerificationReport(
            status="nothing_to_test",
            accepted_stacks=[],
            reverted_stacks={},
            coverage={},
            differential={},
            patch_sha256=patch_sha256(""),
            notes=["no test files were proposed"],
        )

    accepted: list[str] = []
    reverted: dict[str, list[str]] = {}
    coverage: dict[str, dict[str, object]] = {}
    notes: list[str] = list(config.notes)
    baseline_failed = False

    for stack in STACKS:
        if stack not in targeted:
            continue
        gate = _run_stack(config, stack, paths)
        coverage[stack] = {
            "before": gate.coverage_before,
            "after": gate.coverage_after,
            "delta": (
                round(gate.coverage_after - gate.coverage_before, 2)
                if gate.coverage_before is not None and gate.coverage_after is not None
                else None
            ),
            "tests": gate.tests,
            "flaky": gate.flaky,
        }
        if gate.accepted:
            accepted.append(stack)
        else:
            reverted[stack] = list(gate.reasons)
            notes.extend(f"{stack}: {reason}" for reason in gate.reasons)
            if any("baseline failing" in reason for reason in gate.reasons):
                baseline_failed = True

    accepted_paths = [
        path for path in paths if any(path.startswith(f"{stack}/") for stack in accepted)
    ]
    verified_patch = build_patch(config.patch, accepted_paths)

    status: GateStatus
    if accepted:
        status = "passed"
    elif baseline_failed:
        status = "baseline_failing"
    else:
        status = "reverted"

    return VerificationReport(
        status=status,
        accepted_stacks=accepted,
        reverted_stacks=reverted,
        coverage=coverage,
        differential={},
        patch_sha256=patch_sha256(verified_patch),
        notes=notes,
        verified_patch=verified_patch,
    )
