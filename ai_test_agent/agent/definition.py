"""Load `.claude/agents/unit-test-agent.md` as the system prompt."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .skills import FRONTMATTER

REQUIRED_TOOLS = {
    "get_diff",
    "get_coverage",
    "activate_skill",
    "list_files",
    "read_file",
    "write_test_file",
    "run_pytest",
    "run_vitest",
    "finish",
}
DEFAULT_MODEL_KEY = "default"


class DefinitionError(ValueError):
    """The agent definition is missing or malformed."""


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    description: str
    model: str
    tools: list[str]
    system_prompt: str


def load_agent_definition(path: Path, known_tools: set[str]) -> AgentDefinition:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if match is None:
        raise DefinitionError(f"{path}: missing YAML frontmatter")
    metadata = yaml.safe_load(match.group("meta"))
    if not isinstance(metadata, dict):
        raise DefinitionError(f"{path}: frontmatter must be a mapping")

    name = metadata.get("name")
    description = metadata.get("description")
    model = metadata.get("model", DEFAULT_MODEL_KEY)
    tools = metadata.get("tools")
    if not isinstance(name, str) or not name:
        raise DefinitionError(f"{path}: name is required")
    if not isinstance(description, str) or not description:
        raise DefinitionError(f"{path}: description is required")
    if not isinstance(model, str) or not model:
        raise DefinitionError(f"{path}: model is required")
    if not isinstance(tools, list) or not all(isinstance(tool, str) for tool in tools):
        raise DefinitionError(f"{path}: tools must be a list of names")

    unknown = set(tools) - known_tools
    if unknown:
        raise DefinitionError(f"{path}: unknown tools: {', '.join(sorted(unknown))}")
    missing = REQUIRED_TOOLS - set(tools)
    if missing:
        raise DefinitionError(f"{path}: missing tools: {', '.join(sorted(missing))}")

    body = match.group("body").strip()
    if not body:
        raise DefinitionError(f"{path}: system prompt is empty")
    return AgentDefinition(
        name=name,
        description=description,
        model=model,
        tools=tools,
        system_prompt=body,
    )
