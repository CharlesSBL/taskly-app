"""Progressive-disclosure skill loading.

At start-up the model sees only each skill's name and description. Calling
`activate_skill` returns the full body and records the activation in the trace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER = re.compile(r"\A---\s*\n(?P<meta>.*?)\n---\s*\n(?P<body>.*)\Z", re.DOTALL)


class SkillError(ValueError):
    """A skill file is missing, malformed or ambiguous."""


class SkillNotFound(SkillError):
    """The requested skill is not part of the library."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    body: str
    path: Path

    def catalog_entry(self) -> dict[str, str]:
        return {"name": self.name, "description": self.description}


def parse_skill(path: Path) -> Skill:
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if match is None:
        raise SkillError(f"{path}: missing YAML frontmatter")
    try:
        metadata = yaml.safe_load(match.group("meta"))
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise SkillError(f"{path}: invalid frontmatter: {exc}") from exc
    if not isinstance(metadata, dict):
        raise SkillError(f"{path}: frontmatter must be a mapping")

    name = metadata.get("name")
    description = metadata.get("description")
    if not isinstance(name, str) or not isinstance(description, str):
        raise SkillError(f"{path}: frontmatter needs string name and description")
    if not NAME_PATTERN.match(name):
        raise SkillError(f"{path}: invalid skill name {name!r}")
    if path.parent.name != name:
        raise SkillError(f"{path}: directory name does not match skill name {name!r}")

    body = match.group("body").strip()
    if not body:
        raise SkillError(f"{path}: skill body is empty")
    return Skill(name=name, description=description, body=body, path=path)


class SkillLibrary:
    def __init__(self, skills: dict[str, Skill]) -> None:
        self._skills = skills

    @classmethod
    def discover(cls, skills_dir: Path) -> SkillLibrary:
        if not skills_dir.is_dir():
            return cls({})
        skills: dict[str, Skill] = {}
        for path in sorted(skills_dir.glob("*/SKILL.md")):
            skill = parse_skill(path)
            if skill.name in skills:
                raise SkillError(f"duplicate skill name: {skill.name}")
            skills[skill.name] = skill
        return cls(skills)

    def __len__(self) -> int:
        return len(self._skills)

    def names(self) -> list[str]:
        return sorted(self._skills)

    def catalog(self) -> list[dict[str, str]]:
        return [self._skills[name].catalog_entry() for name in self.names()]

    def catalog_prompt(self) -> str:
        if not self._skills:
            return "No skills are available."
        lines = ["Available skills (activate one before using its instructions):"]
        lines.extend(f"- {skill.name}: {skill.description}" for skill in self._skills.values())
        return "\n".join(lines)

    def activate(self, name: str) -> str:
        skill = self._skills.get(name)
        if skill is None:
            available = ", ".join(self.names()) or "none"
            raise SkillNotFound(f"unknown skill {name!r}; available: {available}")
        return skill.body

    def tool_spec(self) -> dict[str, Any]:
        return {
            "name": "activate_skill",
            "description": (
                "Load a skill's full instructions. Start with analyze-diff for each "
                "changed file, then the stack conventions, then test-quality-review."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"name": {"type": "string", "enum": self.names()}},
                "required": ["name"],
            },
        }
