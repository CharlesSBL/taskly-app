from __future__ import annotations

from pathlib import Path

import pytest

from verifier import action_pins

PINNED = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"


def write_workflow(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_pinned_action_passes(tmp_path: Path) -> None:
    path = write_workflow(
        tmp_path,
        f"jobs:\n  build:\n    steps:\n      - uses: {PINNED}\n",
    )
    assert action_pins.check_file(path) == []


def test_tag_reference_fails(tmp_path: Path) -> None:
    path = write_workflow(
        tmp_path,
        "jobs:\n  build:\n    steps:\n      - uses: actions/checkout@v4\n",
    )
    problems = action_pins.check_file(path)
    assert problems == [f"{path}:4: not pinned to a commit SHA: actions/checkout@v4"]


def test_quoted_reference_is_checked(tmp_path: Path) -> None:
    path = write_workflow(
        tmp_path,
        'jobs:\n  build:\n    steps:\n      - uses: "actions/checkout@v4"\n',
    )
    assert action_pins.check_file(path)


def test_local_and_docker_references_are_ignored(tmp_path: Path) -> None:
    path = write_workflow(
        tmp_path,
        "steps:\n  - uses: ./.github/actions/local\n  - uses: docker://alpine:3.20\n",
    )
    assert action_pins.check_file(path) == []


def test_check_paths_walks_directories(tmp_path: Path) -> None:
    workflows = tmp_path / "workflows"
    workflows.mkdir()
    write_workflow(workflows, "steps:\n  - uses: actions/cache@v4\n")
    (workflows / "second.yaml").write_text(f"steps:\n  - uses: {PINNED}\n", encoding="utf-8")
    problems = action_pins.check_paths([workflows])
    assert len(problems) == 1
    assert "actions/cache@v4" in problems[0]


def test_main_returns_failure_and_prints(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_workflow(tmp_path, "steps:\n  - uses: actions/checkout@v4\n")
    assert action_pins.main([str(tmp_path)]) == 1
    assert "not pinned" in capsys.readouterr().err


def test_main_returns_success(tmp_path: Path) -> None:
    write_workflow(tmp_path, f"steps:\n  - uses: {PINNED}\n")
    assert action_pins.main([str(tmp_path)]) == 0
