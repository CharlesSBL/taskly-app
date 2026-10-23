"""Strict schema for `agent_manifest.json`.

The manifest is model output, therefore untrusted. Every consumer validates it
with this schema before reading a single field.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Action = Literal["create", "update", "skip"]
Stack = Literal["backend", "frontend"]
ManifestStatus = Literal[
    "completed",
    "nothing_to_test",
    "budget_exceeded",
    "baseline_failing",
    "error",
]
BaselineStatus = Literal["passed", "failed", "skipped"]


class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file: str = Field(min_length=1)
    action: Action
    rationale: str = Field(min_length=1)
    skill_used: str | None = None
    target_test_file: str | None = None
    test_claims: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_target_for_changes(self) -> Decision:
        if self.action in ("create", "update") and not self.target_test_file:
            raise ValueError(f"{self.action} decision for {self.file} needs a target_test_file")
        return self


class Baseline(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: BaselineStatus
    tests: int | None = Field(default=None, ge=0)
    coverage: float | None = Field(default=None, ge=0, le=100)


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    status: ManifestStatus
    model: str
    decisions: list[Decision] = Field(default_factory=list)
    files_written: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)
    turns: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cost_usd: float = Field(default=0.0, ge=0)
    lockfile_changed: bool = False
    baseline: dict[Stack, Baseline] = Field(default_factory=dict)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

    def write(self, path: Path) -> None:
        path.write_text(self.to_json() + "\n", encoding="utf-8")


def load_manifest(path: Path) -> Manifest:
    """Parse and validate a manifest, raising pydantic's ValidationError."""
    raw: object = json.loads(path.read_text(encoding="utf-8"))
    return Manifest.model_validate(raw)


def empty_manifest(status: ManifestStatus, model: str, **kwargs: Any) -> Manifest:
    return Manifest(status=status, model=model, **kwargs)
