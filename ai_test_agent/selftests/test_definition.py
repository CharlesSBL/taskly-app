from __future__ import annotations

from pathlib import Path

import pytest

from agent.definition import (
    REQUIRED_TOOLS,
    DefinitionError,
    load_agent_definition,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def write_definition(path: Path, frontmatter: str, body: str = "You write tests.") -> Path:
    path.write_text(f"---\n{frontmatter}\n---\n{body}\n", encoding="utf-8")
    return path


def test_repository_definition_loads() -> None:
    definition = load_agent_definition(
        REPO_ROOT / ".claude" / "agents" / "unit-test-agent.md", REQUIRED_TOOLS
    )
    assert definition.name == "unit-test-agent"
    assert definition.model == "default"
    assert set(definition.tools) == REQUIRED_TOOLS
    assert "untrusted_source_data" in definition.system_prompt


def test_unknown_tool_is_rejected(tmp_path: Path) -> None:
    path = write_definition(
        tmp_path / "agent.md",
        "name: a\ndescription: d\nmodel: default\ntools:\n  - get_diff",
    )
    with pytest.raises(DefinitionError, match="unknown tools: get_diff"):
        load_agent_definition(path, set())


def test_missing_required_tools_are_rejected(tmp_path: Path) -> None:
    path = write_definition(
        tmp_path / "agent.md",
        "name: a\ndescription: d\nmodel: default\ntools:\n  - get_diff",
    )
    with pytest.raises(DefinitionError, match="missing tools"):
        load_agent_definition(path, {"get_diff"})


def test_missing_frontmatter_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "agent.md"
    path.write_text("no frontmatter", encoding="utf-8")
    with pytest.raises(DefinitionError, match="frontmatter"):
        load_agent_definition(path, REQUIRED_TOOLS)


def test_non_mapping_frontmatter_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "agent.md"
    path.write_text("---\n- a\n- b\n---\nbody\n", encoding="utf-8")
    with pytest.raises(DefinitionError, match="mapping"):
        load_agent_definition(path, REQUIRED_TOOLS)


@pytest.mark.parametrize(
    ("frontmatter", "message"),
    [
        ("name: ''\ndescription: d\nmodel: default", "name is required"),
        ("name: a\ndescription: ''\nmodel: default", "description is required"),
        ("name: a\ndescription: d\nmodel: ''", "model is required"),
        ("name: a\ndescription: d\nmodel: default\ntools: get_diff", "list of names"),
    ],
)
def test_invalid_fields_are_rejected(tmp_path: Path, frontmatter: str, message: str) -> None:
    path = write_definition(tmp_path / "agent.md", frontmatter)
    with pytest.raises(DefinitionError, match=message):
        load_agent_definition(path, REQUIRED_TOOLS)


def test_empty_body_is_rejected(tmp_path: Path) -> None:
    tools = "\n".join(f"  - {tool}" for tool in sorted(REQUIRED_TOOLS))
    path = write_definition(
        tmp_path / "agent.md",
        f"name: a\ndescription: d\nmodel: default\ntools:\n{tools}",
        body="",
    )
    with pytest.raises(DefinitionError, match="system prompt is empty"):
        load_agent_definition(path, REQUIRED_TOOLS)
