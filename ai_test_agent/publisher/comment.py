"""Render the sticky pull-request comment and the job summary.

The renderer is pure: it takes the validated manifest and verification report
and produces Markdown. The workflow only posts it.
"""

from __future__ import annotations

from agent.manifest import Manifest
from verifier.types import VerificationReport

MARKER = "<!-- ai-unit-test-agent-report -->"
MAX_CELL = 160

ACTIONS = {"create": "➕ create", "update": "♻️ update", "skip": "⏭️ skip"}
STATES = {
    "passed": "✅ Tests verified",
    "nothing_to_test": "⏭️ Nothing to test",
    "baseline_failing": "⚠️ Baseline failing",
    "reverted": "⚠️ Tests reverted",
    "rejected": "🛑 Output rejected",
}
DIFFERENTIAL_LABELS = {
    "true": "✅ Failed on base / passed on PR",
    "false": "⚠️ Passed on both (may not detect regressions)",
    "n/a": "n/a",
}


def _cell(value: str) -> str:
    text = value.replace("|", "\\|").replace("\n", " ").strip()
    if len(text) > MAX_CELL:
        return text[: MAX_CELL - 1] + "…"
    return text


def _state(manifest: Manifest, report: VerificationReport) -> str:
    if report.status == "passed" and manifest.status == "error":
        return "❌ Agent error"
    return STATES.get(report.status, report.status)


def _percent(value: object) -> str:
    return f"{value:.2f}%" if isinstance(value, (int, float)) else "n/a"


def _delta(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "n/a"
    return f"{value:+.2f}%"


def _coverage_table(report: VerificationReport) -> str:
    rows = [
        "| Stack | Before | After | Δ | Tests run | Flaky |",
        "| --- | ---: | ---: | ---: | ---: | :---: |",
    ]
    for stack in sorted(report.coverage):
        entry = report.coverage[stack]
        rows.append(
            "| {stack} | {before} | {after} | {delta} | {tests} | {flaky} |".format(
                stack=stack,
                before=_percent(entry.get("before")),
                after=_percent(entry.get("after")),
                delta=_delta(entry.get("delta")),
                tests=entry.get("tests") if entry.get("tests") is not None else "n/a",
                flaky="yes" if entry.get("flaky") else "no",
            )
        )
    return "\n".join(rows)


def _differential_table(report: VerificationReport) -> str:
    if not report.differential:
        return "_Differential check did not run._"
    rows = ["| Test file | Failed on base |", "| --- | --- |"]
    for path in sorted(report.differential):
        label = DIFFERENTIAL_LABELS.get(report.differential[path], report.differential[path])
        rows.append(f"| `{_cell(path)}` | {label} |")
    return "\n".join(rows)


def _decisions_table(manifest: Manifest) -> str:
    if not manifest.decisions:
        return "_No decisions were recorded._"
    rows = ["| File | Action | Skill | Rationale |", "| --- | --- | --- | --- |"]
    for decision in manifest.decisions:
        rows.append(
            "| `{file}` | {action} | {skill} | {rationale} |".format(
                file=_cell(decision.file),
                action=ACTIONS.get(decision.action, decision.action),
                skill=_cell(decision.skill_used or "—"),
                rationale=_cell(decision.rationale),
            )
        )
    return "\n".join(rows)


def _claims(manifest: Manifest) -> str:
    lines: list[str] = []
    for decision in manifest.decisions:
        if not decision.test_claims:
            continue
        lines.append(f"**`{decision.target_test_file or decision.file}`**")
        lines.extend(f"- {claim}" for claim in decision.test_claims)
    return "\n".join(lines) if lines else "_No behavior claims were made._"


def _warnings(manifest: Manifest, report: VerificationReport) -> list[str]:
    warnings: list[str] = []
    if report.status == "rejected":
        warnings.append(
            "**Rejected:** the agent artifact failed integrity checks. Nothing was accepted."
        )
    if report.reverted_stacks:
        details = "; ".join(
            f"`{stack}`: {reason}"
            for stack, reasons in sorted(report.reverted_stacks.items())
            for reason in reasons[:3]
        )
        warnings.append(f"**Reverted stacks:** {details}")
    if report.status == "baseline_failing":
        warnings.append(
            "A stack's baseline tests are failing; that stack was left untouched. "
            "Fix the baseline before relying on this report."
        )
    if manifest.lockfile_changed:
        warnings.append(
            "**Lockfiles changed.** Dependencies were installed from the base revision; "
            "review dependency changes separately."
        )
    if manifest.status in ("budget_exceeded", "error"):
        warnings.append(
            f"The agent stopped with status `{manifest.status}`; the results may be partial."
        )
    return warnings


def render_comment(
    manifest: Manifest,
    report: VerificationReport,
    *,
    trace_url: str | None = None,
    run_url: str | None = None,
) -> str:
    lines: list[str] = [MARKER, f"## 🤖 AI unit-test agent — {_state(manifest, report)}", ""]

    for warning in _warnings(manifest, report):
        lines.append(f"> [!WARNING]\n> {warning}\n")

    lines.extend(
        [
            "| | |",
            "| --- | --- |",
            f"| Accepted stacks | {', '.join(report.accepted_stacks) or '—'} |",
            f"| Reverted stacks | {', '.join(sorted(report.reverted_stacks)) or '—'} |",
            f"| Model | `{manifest.model}` |",
            f"| Turns | {manifest.turns} |",
            f"| Tokens | {manifest.input_tokens:,} in / {manifest.output_tokens:,} out |",
            f"| Cost | ${manifest.cost_usd:.4f} |",
            f"| Lockfiles changed | {'yes' if manifest.lockfile_changed else 'no'} |",
            "",
            "### Decisions",
            "",
            _decisions_table(manifest),
            "",
            "### Coverage",
            "",
            _coverage_table(report),
            "",
            "### Differential: did the tests fail on the base?",
            "",
            _differential_table(report),
            "",
            "### What the tests claim to verify",
            "",
            _claims(manifest),
            "",
        ]
    )

    if report.verified_patch:
        lines.extend(
            [
                f"### Verified patch (`sha256: {report.patch_sha256}`)",
                "",
                "The default is patch-only: review it, or add the `ai-tests:commit` label "
                "to let a maintainer commit it.",
                "",
                "<details><summary>📋 Verified test patch (git apply)</summary>",
                "",
                "````diff",
                report.verified_patch.rstrip(),
                "````",
                "",
                "</details>",
                "",
            ]
        )
    else:
        lines.extend(["### Verified patch", "", "_No patch was accepted._", ""])

    footer = [
        "---",
        "Trace: "
        + (f"[agent_trace.json]({trace_url})" if trace_url else "see the workflow artifacts"),
    ]
    if run_url:
        footer.append(f"Workflow run: [details]({run_url})")
    lines.append(" · ".join(footer))
    return "\n".join(lines)


def render_step_summary(manifest: Manifest, report: VerificationReport) -> str:
    return render_comment(manifest, report)
