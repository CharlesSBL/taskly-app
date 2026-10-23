from __future__ import annotations

import json
from pathlib import Path

from agent.budget import Usage
from agent.tracing import MAX_FIELD_CHARS, Trace, truncate


def test_trace_records_turns_tools_and_skills(tmp_path: Path) -> None:
    trace = Trace(model="claude-sonnet-5-5")
    turn = trace.start_turn(1, "tool_use", "I will inspect the diff.")
    trace.record_tool(
        turn,
        "read_file",
        {"path": "backend/app/x.py"},
        "secret sk-ant-api03-abcdefghijklmnop",
        error=False,
    )
    trace.activate_skill("analyze-diff")
    trace.usage = Usage(input_tokens=10, output_tokens=5)
    trace.cost_usd = 0.001

    path = tmp_path / "agent_trace.json"
    trace.write(path)
    raw = json.loads(path.read_text())

    assert raw["skills_activated"] == ["analyze-diff"]
    assert raw["turns"][0]["tool_calls"][0]["name"] == "read_file"
    assert "sk-ant" not in json.dumps(raw)
    assert raw["usage"]["input_tokens"] == 10
    assert raw["cost_usd"] == 0.001


def test_long_fields_are_truncated() -> None:
    long_text = "x" * (MAX_FIELD_CHARS + 50)
    result = truncate(long_text)
    assert result.startswith("x" * 100)
    assert "truncated 50 chars" in result
    assert len(result) < len(long_text)


def test_short_fields_are_untouched() -> None:
    assert truncate("hello") == "hello"
