"""A redacted, bounded record of what the agent did.

The trace is uploaded as an artifact so a human can audit a run. It must never
contain the API key, raw repository content beyond small excerpts, or
unbounded tool output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .budget import Usage
from .redaction import redact, redact_text

MAX_FIELD_CHARS = 2000


def truncate(value: str, limit: int = MAX_FIELD_CHARS) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}… [truncated {len(value) - limit} chars]"


@dataclass
class ToolCall:
    name: str
    arguments: str
    result: str
    is_error: bool = False


@dataclass
class Turn:
    index: int
    stop_reason: str | None = None
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class Trace:
    model: str
    turns: list[Turn] = field(default_factory=list)
    skills_activated: list[str] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    cost_usd: float = 0.0
    notes: list[str] = field(default_factory=list)

    def start_turn(self, index: int, stop_reason: str | None, text: str) -> Turn:
        turn = Turn(index=index, stop_reason=stop_reason, text=truncate(text))
        self.turns.append(turn)
        return turn

    def record_tool(
        self, turn: Turn, name: str, arguments: Any, result: str, *, error: bool
    ) -> None:
        turn.tool_calls.append(
            ToolCall(
                name=name,
                arguments=truncate(redact_text(json.dumps(redact(arguments), default=str))),
                result=truncate(redact_text(result)),
                is_error=error,
            )
        )

    def activate_skill(self, name: str) -> None:
        self.skills_activated.append(name)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "skills_activated": redact(self.skills_activated),
            "turns": [
                {
                    "index": turn.index,
                    "stop_reason": turn.stop_reason,
                    "text": redact_text(turn.text),
                    "tool_calls": [
                        {
                            "name": call.name,
                            "arguments": call.arguments,
                            "result": call.result,
                            "is_error": call.is_error,
                        }
                        for call in turn.tool_calls
                    ],
                }
                for turn in self.turns
            ],
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "cache_creation_input_tokens": self.usage.cache_creation_input_tokens,
                "cache_read_input_tokens": self.usage.cache_read_input_tokens,
            },
            "cost_usd": round(self.cost_usd, 6),
            "notes": redact(self.notes),
        }

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
