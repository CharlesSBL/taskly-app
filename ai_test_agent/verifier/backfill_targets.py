"""Pick the lowest-coverage modules for a backfill run.

Selection is deliberately simple and deterministic: sort by coverage
ascending, then by path, and take a bounded number of files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

BACKEND_EXCLUDED = ("__init__.py", "models.py", "schemas.py", "main.py")
FRONTEND_EXCLUDED_MARKERS = (
    ".test.",
    ".stories.",
    "/types.ts",
    "/index.ts",
    "/constants.ts",
    "/design-system/",
    "/test/",
    "/main.tsx",
)


def _limit(value: int) -> int:
    return max(0, min(value, 30))


def select_backend_targets(payload: dict[str, Any], limit: int) -> list[str]:
    files = payload.get("files", {})
    if not isinstance(files, dict):
        return []
    candidates: list[tuple[float, str]] = []
    for name, entry in files.items():
        if not isinstance(name, str) or not name.startswith("app/"):
            continue
        if name.endswith(BACKEND_EXCLUDED):
            continue
        summary = entry.get("summary", {}) if isinstance(entry, dict) else {}
        percent = summary.get("percent_covered")
        statements = summary.get("num_statements", 0)
        if not isinstance(percent, (int, float)) or not isinstance(statements, int):
            continue
        if statements <= 0:
            continue
        candidates.append((float(percent), f"backend/{name}"))
    candidates.sort()
    return [path for _, path in candidates[: _limit(limit)]]


def _relative_frontend(name: str) -> str | None:
    marker = "frontend/src/"
    index = name.find(marker)
    if index == -1:
        return None
    relative = name[index:]
    if any(part in relative for part in FRONTEND_EXCLUDED_MARKERS):
        return None
    return relative


def select_frontend_targets(payload: dict[str, Any], limit: int) -> list[str]:
    candidates: list[tuple[float, str]] = []
    for name, entry in payload.items():
        if name == "total" or not isinstance(name, str):
            continue
        relative = _relative_frontend(name)
        if relative is None:
            continue
        lines = entry.get("lines", {}) if isinstance(entry, dict) else {}
        percent = lines.get("pct") if isinstance(lines, dict) else None
        if not isinstance(percent, (int, float)):
            continue
        candidates.append((float(percent), relative))
    candidates.sort()
    return [path for _, path in candidates[: _limit(limit)]]


def select_targets(
    stack: str, backend: dict[str, Any], frontend: dict[str, Any], limit: int
) -> list[str]:
    cap = _limit(limit)
    if stack == "backend":
        return select_backend_targets(backend, cap)
    if stack == "frontend":
        return select_frontend_targets(frontend, cap)
    if cap == 0:
        return []
    backend_quota = max(1, cap // 2)
    frontend_quota = max(1, cap - backend_quota) if cap > 1 else 0
    selected = select_backend_targets(backend, backend_quota)
    selected.extend(select_frontend_targets(frontend, frontend_quota))
    return selected[:cap]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m verifier.backfill_targets")
    parser.add_argument("--stack", choices=["backend", "frontend", "both"], required=True)
    parser.add_argument("--backend-coverage", type=Path)
    parser.add_argument("--frontend-coverage", type=Path)
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    backend = (
        json.loads(args.backend_coverage.read_text())
        if args.backend_coverage and args.backend_coverage.is_file()
        else {}
    )
    frontend = (
        json.loads(args.frontend_coverage.read_text())
        if args.frontend_coverage and args.frontend_coverage.is_file()
        else {}
    )
    targets = select_targets(args.stack, backend, frontend, args.limit)
    args.out.write_text("".join(f"{target}\n" for target in targets), encoding="utf-8")
    print(f"{len(targets)} targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
