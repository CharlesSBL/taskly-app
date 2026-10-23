"""Parse coverage reports produced inside the sandbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _percentage(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    return None


def backend_percentage(payload: dict[str, Any]) -> float | None:
    totals = payload.get("totals", {})
    if not isinstance(totals, dict):
        return None
    return _percentage(totals.get("percent_covered"))


def frontend_percentage(payload: dict[str, Any]) -> float | None:
    total = payload.get("total", {})
    if not isinstance(total, dict):
        return None
    lines = total.get("lines", {})
    if not isinstance(lines, dict):
        return None
    return _percentage(lines.get("pct"))


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def read_backend(report_dir: Path) -> float | None:
    payload = read_json(report_dir / "be_coverage.json")
    return backend_percentage(payload) if payload is not None else None


def read_frontend(report_dir: Path) -> float | None:
    payload = read_json(report_dir / "fe_coverage" / "coverage-summary.json")
    return frontend_percentage(payload) if payload is not None else None


def read_coverage(report_dir: Path, stack: str) -> float | None:
    return read_backend(report_dir) if stack == "backend" else read_frontend(report_dir)
