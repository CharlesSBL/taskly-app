"""Structural regression tests for the workflows.

These guard the two workflow defects found during live testing: the
verification gate was skipped when an upstream job was skipped, and the
artifact download nested the artifact under an extra directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

WORKFLOW_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"
WORKFLOWS = ("unit-test-agent.yml", "coverage-backfill.yml")


def load(name: str) -> dict[str, Any]:
    payload = yaml.safe_load((WORKFLOW_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def steps(name: str) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for job in load(name)["jobs"].values():
        collected.extend(job.get("steps", []))
    return collected


def test_verifier_always_runs_after_the_agent_job() -> None:
    gate = load("unit-test-agent.yml")["jobs"]["verify-gate"]
    assert gate["needs"] == ["agent-run"]
    assert str(gate["if"]).strip() == "always()"


def test_artifact_downloads_are_not_nested_under_a_path() -> None:
    for name in WORKFLOWS:
        for step in steps(name):
            if not str(step.get("uses", "")).startswith("actions/download-artifact"):
                continue
            assert "path" not in (step.get("with") or {}), f"{name}: {step['name']}"


def test_job_dependencies_reference_existing_jobs() -> None:
    for name in WORKFLOWS:
        jobs = load(name)["jobs"]
        for job_name, job in jobs.items():
            needs = job.get("needs") or []
            if isinstance(needs, str):
                needs = [needs]
            for dependency in needs:
                assert dependency in jobs, f"{name}: {job_name} needs {dependency}"
