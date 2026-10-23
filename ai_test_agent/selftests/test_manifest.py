from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from agent.manifest import Baseline, Decision, Manifest, empty_manifest, load_manifest


def test_create_and_update_require_a_target_test_file() -> None:
    with pytest.raises(ValidationError, match="target_test_file"):
        Decision(file="backend/app/x.py", action="create", rationale="new logic")
    decision = Decision(
        file="backend/app/x.py",
        action="create",
        rationale="new logic",
        target_test_file="backend/tests/test_x.py",
    )
    assert decision.test_claims == []


def test_skip_does_not_require_a_target() -> None:
    decision = Decision(file="README.md", action="skip", rationale="documentation")
    assert decision.target_test_file is None


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Decision.model_validate(
            {"file": "a.py", "action": "skip", "rationale": "docs", "unexpected": True}
        )
    with pytest.raises(ValidationError):
        Manifest.model_validate({"status": "completed", "model": "m", "surprise": 1})


def test_baseline_bounds() -> None:
    with pytest.raises(ValidationError):
        Baseline(status="passed", coverage=140)


def test_manifest_roundtrip(tmp_path: Path) -> None:
    manifest = empty_manifest(
        "completed",
        "claude-sonnet-5-5",
        decisions=[Decision(file="a.py", action="skip", rationale="docs")],
        baseline={"backend": Baseline(status="passed", tests=21, coverage=42.0)},
        turns=2,
        input_tokens=100,
        output_tokens=50,
        cost_usd=0.0123,
    )
    path = tmp_path / "agent_manifest.json"
    manifest.write(path)

    loaded = load_manifest(path)
    assert loaded == manifest
    raw = json.loads(path.read_text())
    assert raw["schema_version"] == 1
    assert raw["baseline"]["backend"]["coverage"] == 42.0


def test_negative_tokens_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Manifest(status="completed", model="m", input_tokens=-1)
