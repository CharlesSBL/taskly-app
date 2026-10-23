from __future__ import annotations

import subprocess
from pathlib import Path

from agent.patch import build_candidate_patch


def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "backend/tests").mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    return repo


def test_patch_contains_new_test_files(tmp_path: Path) -> None:
    repo = git_repo(tmp_path)
    (repo / "backend/tests/test_new.py").write_text("def test_x():\n    assert 1 == 1\n")
    destination = tmp_path / "candidate.patch"

    build_candidate_patch(repo, ["backend/tests/test_new.py"], destination)

    patch = destination.read_text(encoding="utf-8")
    assert "new file mode" in patch
    assert "+++ b/backend/tests/test_new.py" in patch
    assert "+def test_x():" in patch


def test_empty_file_list_produces_an_empty_patch(tmp_path: Path) -> None:
    destination = tmp_path / "candidate.patch"
    build_candidate_patch(tmp_path, [], destination)
    assert destination.read_text(encoding="utf-8") == ""
