"""Shared result types for the verification gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from agent.manifest import Stack

GateStatus = Literal["passed", "nothing_to_test", "baseline_failing", "reverted", "rejected"]


@dataclass(frozen=True)
class Issue:
    path: str
    message: str
    line: int | None = None

    def as_text(self) -> str:
        location = f"{self.path}:{self.line}" if self.line else self.path
        return f"{location}: {self.message}"


@dataclass
class StackGate:
    stack: Stack
    accepted: bool = False
    reasons: list[str] = field(default_factory=list)
    coverage_before: float | None = None
    coverage_after: float | None = None
    tests: int | None = None
    flaky: bool = False

    def reject(self, reason: str) -> None:
        self.accepted = False
        self.reasons.append(reason)

    def as_dict(self) -> dict[str, object]:
        return {
            "stack": self.stack,
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "coverage_before": self.coverage_before,
            "coverage_after": self.coverage_after,
            "tests": self.tests,
            "flaky": self.flaky,
        }


@dataclass(frozen=True)
class CoverageDelta:
    stack: Stack
    before: float | None
    after: float | None

    @property
    def delta(self) -> float | None:
        if self.before is None or self.after is None:
            return None
        return round(self.after - self.before, 2)

    def as_dict(self) -> dict[str, object]:
        return {
            "stack": self.stack,
            "before": self.before,
            "after": self.after,
            "delta": self.delta,
        }


@dataclass
class VerificationReport:
    status: GateStatus
    accepted_stacks: list[str]
    reverted_stacks: dict[str, list[str]]
    coverage: dict[str, dict[str, object]]
    differential: dict[str, str]
    patch_sha256: str
    notes: list[str] = field(default_factory=list)

    # The patch itself is not serialized into the report; it is written to disk
    # next to this JSON so the sha256 can be re-verified by the publisher.
    verified_patch: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "accepted_stacks": list(self.accepted_stacks),
            "reverted_stacks": {key: list(value) for key, value in self.reverted_stacks.items()},
            "coverage": dict(self.coverage),
            "differential": dict(self.differential),
            "patch_sha256": self.patch_sha256,
            "notes": list(self.notes),
        }
