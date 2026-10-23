from __future__ import annotations

import json
from pathlib import Path

from verifier.backfill_targets import (
    main,
    select_backend_targets,
    select_frontend_targets,
    select_targets,
)

BACKEND = {
    "files": {
        "app/core/config.py": {"summary": {"percent_covered": 0.0, "num_statements": 10}},
        "app/core/lifespan.py": {"summary": {"percent_covered": 10.0, "num_statements": 10}},
        "app/api/health.py": {"summary": {"percent_covered": 0.0, "num_statements": 5}},
        "app/features/todos/router.py": {
            "summary": {"percent_covered": 51.0, "num_statements": 20}
        },
        "app/features/todos/models.py": {"summary": {"percent_covered": 0.0, "num_statements": 5}},
        "app/features/todos/__init__.py": {
            "summary": {"percent_covered": 0.0, "num_statements": 1}
        },
        "app/core/empty.py": {"summary": {"percent_covered": 0.0, "num_statements": 0}},
    }
}

FRONTEND = {
    "/repo/frontend/src/lib/http.ts": {"lines": {"pct": 0}},
    "/repo/frontend/src/hooks/useNotice.ts": {"lines": {"pct": 54.5}},
    "/repo/frontend/src/features/todos/components/TodoList.tsx": {"lines": {"pct": 20}},
    "/repo/frontend/src/features/todos/components/TodoList.test.tsx": {"lines": {"pct": 0}},
    "/repo/frontend/src/design-system/Button/Button.tsx": {"lines": {"pct": 0}},
    "/repo/frontend/src/features/todos/types.ts": {"lines": {"pct": 0}},
    "/repo/frontend/src/main.tsx": {"lines": {"pct": 0}},
    "total": {"lines": {"pct": 46.42}},
}


def test_backend_targets_sorted_and_filtered() -> None:
    assert select_backend_targets(BACKEND, 10) == [
        "backend/app/api/health.py",
        "backend/app/core/config.py",
        "backend/app/core/lifespan.py",
        "backend/app/features/todos/router.py",
    ]


def test_backend_limit() -> None:
    assert len(select_backend_targets(BACKEND, 2)) == 2
    assert select_backend_targets(BACKEND, 0) == []


def test_frontend_targets_and_exclusions() -> None:
    assert select_frontend_targets(FRONTEND, 10) == [
        "frontend/src/lib/http.ts",
        "frontend/src/features/todos/components/TodoList.tsx",
        "frontend/src/hooks/useNotice.ts",
    ]


def test_combined_selection_and_cap() -> None:
    selected = select_targets("both", BACKEND, FRONTEND, 2)
    assert len(selected) <= 4
    assert any(path.startswith("backend/") for path in selected)
    assert any(path.startswith("frontend/") for path in selected)


def test_cli_writes_targets(tmp_path: Path) -> None:
    backend_path = tmp_path / "be.json"
    frontend_path = tmp_path / "fe.json"
    backend_path.write_text(json.dumps(BACKEND))
    frontend_path.write_text(json.dumps(FRONTEND))
    out = tmp_path / "targets.txt"

    code = main(
        [
            "--stack",
            "both",
            "--backend-coverage",
            str(backend_path),
            "--frontend-coverage",
            str(frontend_path),
            "--limit",
            "3",
            "--out",
            str(out),
        ]
    )

    assert code == 0
    lines = out.read_text().splitlines()
    assert "backend/app/api/health.py" in lines
    assert "frontend/src/lib/http.ts" in lines


def test_cli_tolerates_missing_reports(tmp_path: Path) -> None:
    out = tmp_path / "targets.txt"
    assert main(["--stack", "backend", "--limit", "3", "--out", str(out)]) == 0
    assert out.read_text() == ""
