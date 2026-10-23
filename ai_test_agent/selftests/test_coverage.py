from __future__ import annotations

import json
from pathlib import Path

from verifier.coverage import (
    backend_percentage,
    frontend_percentage,
    read_backend,
    read_coverage,
    read_frontend,
)


def test_backend_percentage() -> None:
    assert backend_percentage({"totals": {"percent_covered": 42.346}}) == 42.35
    assert backend_percentage({"totals": {"percent_covered": "x"}}) is None
    assert backend_percentage({"totals": []}) is None
    assert backend_percentage({}) is None


def test_frontend_percentage() -> None:
    assert frontend_percentage({"total": {"lines": {"pct": 46.42}}}) == 46.42
    assert frontend_percentage({"total": {"lines": {"pct": "x"}}}) is None
    assert frontend_percentage({"total": "nope"}) is None
    assert frontend_percentage({}) is None


def test_read_reports(tmp_path: Path) -> None:
    (tmp_path / "be_coverage.json").write_text(json.dumps({"totals": {"percent_covered": 61.0}}))
    fe = tmp_path / "fe_coverage"
    fe.mkdir()
    (fe / "coverage-summary.json").write_text(json.dumps({"total": {"lines": {"pct": 70.5}}}))
    assert read_backend(tmp_path) == 61.0
    assert read_frontend(tmp_path) == 70.5
    assert read_coverage(tmp_path, "backend") == 61.0
    assert read_coverage(tmp_path, "frontend") == 70.5


def test_missing_or_invalid_reports(tmp_path: Path) -> None:
    assert read_backend(tmp_path) is None
    (tmp_path / "be_coverage.json").write_text("not json")
    assert read_backend(tmp_path) is None
    (tmp_path / "be_coverage.json").write_text("[]")
    assert read_backend(tmp_path) is None
