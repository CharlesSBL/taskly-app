from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from agent.budget import BudgetGuard
from agent.config import Budgets
from agent.manifest import Stack
from agent.skills import SkillError, SkillLibrary, SkillNotFound, parse_skill
from agent.tools import ToolContext, build_tool_specs, execute
from agent.tools.execution import CommandResult
from agent.tracing import Trace


def write_skill(
    root: Path, name: str, description: str = "Useful skill", body: str = "Do the thing."
) -> Path:
    directory = root / name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def test_discover_returns_catalog_without_bodies(tmp_path: Path) -> None:
    write_skill(tmp_path, "analyze-diff", "Decide what to test")
    library = SkillLibrary.discover(tmp_path)
    assert len(library) == 1
    assert library.names() == ["analyze-diff"]
    assert library.catalog() == [{"name": "analyze-diff", "description": "Decide what to test"}]
    assert "Do the thing." not in library.catalog_prompt()
    assert "analyze-diff: Decide what to test" in library.catalog_prompt()


def test_activate_returns_full_body_without_frontmatter(tmp_path: Path) -> None:
    write_skill(tmp_path, "analyze-diff", body="# Steps\n\nRead the diff.")
    library = SkillLibrary.discover(tmp_path)
    body = library.activate("analyze-diff")
    assert body.startswith("# Steps")
    assert "name: analyze-diff" not in body


def test_unknown_skill_is_rejected(tmp_path: Path) -> None:
    library = SkillLibrary.discover(tmp_path)
    with pytest.raises(SkillNotFound, match="available: none"):
        library.activate("missing")


def test_missing_directory_is_an_empty_library(tmp_path: Path) -> None:
    library = SkillLibrary.discover(tmp_path / "nope")
    assert len(library) == 0
    assert library.catalog_prompt() == "No skills are available."


def test_invalid_frontmatter_is_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "broken"
    directory.mkdir()
    (directory / "SKILL.md").write_text("no frontmatter here", encoding="utf-8")
    with pytest.raises(SkillError, match="frontmatter"):
        SkillLibrary.discover(tmp_path)


def test_name_must_match_directory(tmp_path: Path) -> None:
    directory = tmp_path / "wrong"
    directory.mkdir()
    (directory / "SKILL.md").write_text(
        "---\nname: right\ndescription: x\n---\nbody\n", encoding="utf-8"
    )
    with pytest.raises(SkillError, match="does not match"):
        SkillLibrary.discover(tmp_path)


def test_missing_fields_and_empty_body_are_rejected(tmp_path: Path) -> None:
    directory = tmp_path / "partial"
    directory.mkdir()
    path = directory / "SKILL.md"
    path.write_text("---\nname: partial\n---\nbody\n", encoding="utf-8")
    with pytest.raises(SkillError, match="needs string name and description"):
        parse_skill(path)

    path.write_text("---\nname: partial\ndescription: x\n---\n\n", encoding="utf-8")
    with pytest.raises(SkillError, match="body is empty"):
        parse_skill(path)


def test_nested_directory_name_mismatch_is_rejected(tmp_path: Path) -> None:
    write_skill(tmp_path, "same")
    # Two directories cannot share a name, so simulate a duplicate by
    # parsing one file under a second path.
    other = tmp_path / "nested"
    other.mkdir()
    source = (tmp_path / "same" / "SKILL.md").read_text(encoding="utf-8")
    (other / "SKILL.md").write_text(source, encoding="utf-8")
    with pytest.raises(SkillError, match="does not match"):
        SkillLibrary.discover(tmp_path)


class _Sandbox:
    def run(
        self,
        stack: Stack,
        paths: Sequence[str],
        *,
        coverage: bool = False,
        typecheck: bool = False,
    ) -> CommandResult:
        return CommandResult(returncode=0, output="")


def make_context(tmp_path: Path, library: SkillLibrary) -> ToolContext:
    return ToolContext(
        repo_root=tmp_path,
        diff_path=tmp_path / "diff",
        out_dir=tmp_path,
        guard=BudgetGuard(budgets=Budgets()),
        sandbox=_Sandbox(),
        skills=library,
        trace=Trace(model="claude-sonnet-5-5"),
    )


def test_activate_skill_tool_records_the_activation(tmp_path: Path) -> None:
    write_skill(tmp_path, "analyze-diff", body="Read every changed file.")
    library = SkillLibrary.discover(tmp_path)
    context = make_context(tmp_path, library)
    result = execute(context, "activate_skill", {"name": "analyze-diff"})
    assert result == "Read every changed file."
    assert context.trace is not None
    assert context.trace.skills_activated == ["analyze-diff"]


def test_activate_skill_errors_are_returned_as_text(tmp_path: Path) -> None:
    library = SkillLibrary.discover(tmp_path)
    context = make_context(tmp_path, library)
    result = execute(context, "activate_skill", {"name": "nope"})
    assert result.startswith("ERROR:")
    assert "available: none" in result


def test_tool_specs_include_the_skill_enum(tmp_path: Path) -> None:
    write_skill(tmp_path, "analyze-diff")
    library = SkillLibrary.discover(tmp_path)
    specs = build_tool_specs(library)
    skill_spec = next(spec for spec in specs if spec["name"] == "activate_skill")
    assert skill_spec["input_schema"]["properties"]["name"]["enum"] == ["analyze-diff"]
    assert build_tool_specs(None) == build_tool_specs()
    assert all(spec["name"] != "activate_skill" for spec in build_tool_specs(None))


def test_repository_skills_are_discoverable_and_grounded() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    library = SkillLibrary.discover(repo_root / ".claude" / "skills")
    assert library.names() == [
        "analyze-diff",
        "backend-pytest-conventions",
        "frontend-vitest-conventions",
        "test-quality-review",
    ]
    assert "backend/tests/conftest.py" in library.activate("backend-pytest-conventions")
    assert "frontend/src/design-system/mocks.tsx" in library.activate("frontend-vitest-conventions")
    assert "tooling path" in library.activate("analyze-diff")
