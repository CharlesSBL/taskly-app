"""Prompt assembly for the agent."""

from __future__ import annotations

from .config import Settings
from .definition import AgentDefinition
from .manifest import Baseline, Stack
from .skills import SkillLibrary

STACK_LABELS: dict[Stack, str] = {"backend": "FastAPI/pytest", "frontend": "React/Vitest"}


def build_system_prompt(
    definition: AgentDefinition, settings: Settings, skills: SkillLibrary
) -> str:
    budgets = settings.budgets
    runtime = (
        "## Runtime\n"
        f"- Model: {settings.model}\n"
        f"- Budgets: {budgets.max_turns} turns, {budgets.max_files} files, "
        f"${budgets.max_cost_usd} per run, diff up to {budgets.max_diff_bytes} bytes\n"
        "- Repository: taskly-app (backend: FastAPI + SQLAlchemy; "
        "frontend: React + TypeScript + Vitest)\n"
    )
    return f"{definition.system_prompt}\n\n{runtime}\n{skills.catalog_prompt()}"


def build_user_prompt(
    *,
    mode: str,
    changed_files: list[str],
    baseline: dict[Stack, Baseline],
    lockfile_changed: bool,
    backfill_targets: list[str],
) -> str:
    lines: list[str] = []
    if mode == "backfill":
        lines.append("Coverage backfill run. Add missing unit tests for:")
        lines.extend(f"- {target}" for target in backfill_targets)
        lines.append("")
        lines.append("Inspect each module and its existing tests before writing.")
    else:
        lines.append(f"Pull request with {len(changed_files)} changed files:")
        lines.extend(f"- {path}" for path in changed_files)
        lines.append("")
        lines.append("Start with get_diff, then analyze every changed file.")

    for stack, status in sorted(baseline.items()):
        details: list[str] = [status.status]
        if status.tests is not None:
            details.append(f"{status.tests} tests")
        if status.coverage is not None:
            details.append(f"{status.coverage:.2f}% coverage")
        lines.append(f"Baseline {stack} ({STACK_LABELS[stack]}): {', '.join(details)}")
        if status.status == "failed":
            lines.append(f"  The {stack} baseline is failing: do not modify or test {stack} code.")
    lines.append(f"Lockfiles changed: {'yes' if lockfile_changed else 'no'}.")
    return "\n".join(lines)
