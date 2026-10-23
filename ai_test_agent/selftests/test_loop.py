from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from agent.config import Budgets, Settings
from agent.definition import REQUIRED_TOOLS, AgentDefinition
from agent.loop import AgentRuntime, AnthropicClient, parse_decisions, run_agent
from agent.manifest import Stack
from agent.skills import SkillLibrary
from agent.tools.execution import CommandResult


class FakeMessages:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        # The loop keeps appending to its message list; snapshot it here.
        snapshot = dict(kwargs)
        snapshot["messages"] = list(kwargs.get("messages", []))
        self.calls.append(snapshot)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.messages = FakeMessages(responses)


class FakeSandbox:
    def __init__(self, result: CommandResult | None = None) -> None:
        self.result = result or CommandResult(returncode=0, output="1 passed")
        self.calls: list[tuple[str, list[str], bool]] = []

    def run(self, stack: Stack, paths: Sequence[str], *, coverage: bool = False) -> CommandResult:
        self.calls.append((stack, list(paths), coverage))
        return self.result


def usage(input_tokens: int = 1000, output_tokens: int = 200) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=0,
        cache_read_input_tokens=0,
    )


def text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def tool_block(name: str, arguments: dict[str, Any], tool_id: str = "tool-1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=arguments)


def message(
    *blocks: SimpleNamespace, usage_block: SimpleNamespace | None = None, stop: str = "tool_use"
) -> SimpleNamespace:
    return SimpleNamespace(content=list(blocks), stop_reason=stop, usage=usage_block or usage())


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "backend/app").mkdir(parents=True)
    (repo / "backend/tests").mkdir(parents=True)
    (repo / "backend/app/feature.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / "backend/tests/__init__.py").write_text("")
    diff = tmp_path / "pr.diff"
    diff.write_text("diff --git a/backend/app/feature.py b/backend/app/feature.py\n")
    return repo


def make_skills(tmp_path: Path) -> SkillLibrary:
    directory = tmp_path / "skills" / "analyze-diff"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text(
        "---\nname: analyze-diff\ndescription: Analyze\n---\nRead the diff.\n"
    )
    return SkillLibrary.discover(tmp_path / "skills")


def make_runtime(
    tmp_path: Path,
    client: FakeClient,
    *,
    budgets: Budgets | None = None,
    tools: list[str] | None = None,
) -> AgentRuntime:
    definition = AgentDefinition(
        name="unit-test-agent",
        description="test",
        model="default",
        tools=tools or sorted(REQUIRED_TOOLS),
        system_prompt="You write tests.",
    )
    return AgentRuntime(
        settings=Settings(budgets=budgets or Budgets()),
        client=cast(AnthropicClient, client),
        definition=definition,
        skills=make_skills(tmp_path),
        repo_root=make_repo(tmp_path),
        diff_path=tmp_path / "pr.diff",
        out_dir=tmp_path,
        sandbox=FakeSandbox(),
    )


def finish(*decisions: dict[str, Any]) -> SimpleNamespace:
    return tool_block("finish", {"decisions": list(decisions)})


VALID_DECISION = {
    "file": "backend/app/feature.py",
    "action": "update",
    "rationale": "adds a branch",
    "skill_used": "analyze-diff",
    "target_test_file": "backend/tests/test_feature.py",
    "test_claims": ["adds two numbers"],
}


def test_full_run_records_tools_skills_and_cost(tmp_path: Path) -> None:
    client = FakeClient(
        [
            message(tool_block("get_diff", {})),
            message(tool_block("activate_skill", {"name": "analyze-diff"}, "tool-2")),
            message(
                tool_block(
                    "write_test_file",
                    {
                        "path": "backend/tests/test_feature.py",
                        "content": "def test_add():\n    assert 1 + 1 == 2\n",
                    },
                    "tool-3",
                )
            ),
            message(
                tool_block(
                    "run_pytest",
                    {"paths": ["backend/tests/test_feature.py"]},
                    "tool-4",
                )
            ),
            message(finish(VALID_DECISION), stop="tool_use"),
        ]
    )
    runtime = make_runtime(tmp_path, client)
    result = run_agent(runtime, "PR with one file")

    assert result.manifest.status == "completed"
    assert result.manifest.files_written == ["backend/tests/test_feature.py"]
    assert [decision.action for decision in result.manifest.decisions] == ["update"]
    assert result.manifest.skills_used == ["analyze-diff"]
    assert result.manifest.turns == 5
    assert result.manifest.input_tokens == 5000
    assert result.manifest.output_tokens == 1000
    assert result.manifest.cost_usd == pytest.approx(0.02)
    assert (runtime.repo_root / "backend/tests/test_feature.py").is_file()

    assert len(result.trace.turns) == 5
    assert [call.name for call in result.trace.turns[0].tool_calls] == ["get_diff"]
    assert result.trace.skills_activated == ["analyze-diff"]
    assert result.trace.cost_usd == pytest.approx(0.02)

    first_call = client.messages.calls[0]
    assert first_call["model"] == "claude-sonnet-5-5"
    assert first_call["messages"] == [{"role": "user", "content": "PR with one file"}]
    tool_names = {spec["name"] for spec in first_call["tools"]}
    assert "finish" in tool_names
    assert "activate_skill" in tool_names


def test_cost_budget_stops_before_a_second_call(tmp_path: Path) -> None:
    expensive = message(
        text_block("thinking"), usage_block=usage(input_tokens=1_000_000, output_tokens=0)
    )
    client = FakeClient([expensive])
    runtime = make_runtime(tmp_path, client, budgets=Budgets(max_cost_usd=Decimal("0.50")))

    result = run_agent(runtime, "prompt")

    assert result.manifest.status == "budget_exceeded"
    assert result.manifest.cost_usd == pytest.approx(2.0)
    assert len(client.messages.calls) == 1
    assert result.trace.notes == ["cost limit reached ($2.0000 > $0.50)"]


def test_turn_limit_is_enforced(tmp_path: Path) -> None:
    client = FakeClient([message(tool_block("get_diff", {})), message(tool_block("get_diff", {}))])
    runtime = make_runtime(tmp_path, client, budgets=Budgets(max_turns=2))

    result = run_agent(runtime, "prompt")

    assert result.manifest.status == "budget_exceeded"
    assert result.manifest.turns == 2
    assert "turn limit reached" in result.trace.notes[0]


def test_model_stopping_without_finish_is_an_error(tmp_path: Path) -> None:
    client = FakeClient([message(text_block("I am done"), stop="end_turn")])
    result = run_agent(make_runtime(tmp_path, client), "prompt")
    assert result.manifest.status == "error"
    assert any("without calling finish" in note for note in result.trace.notes)


def test_invalid_finish_is_reported_and_can_be_retried(tmp_path: Path) -> None:
    client = FakeClient(
        [
            message(
                finish({"file": "backend/app/feature.py", "action": "create", "rationale": "x"})
            ),
            message(finish(VALID_DECISION), stop="end_turn"),
        ]
    )
    result = run_agent(make_runtime(tmp_path, client), "prompt")
    assert result.manifest.status == "completed"
    first_result = result.trace.turns[0].tool_calls[0]
    assert first_result.is_error
    assert "target_test_file" in first_result.result


def test_empty_finish_is_reported_and_can_be_retried(tmp_path: Path) -> None:
    client = FakeClient(
        [
            message(finish()),
            message(finish({"file": "README.md", "action": "skip", "rationale": "docs"})),
        ]
    )
    result = run_agent(make_runtime(tmp_path, client), "prompt")
    assert result.manifest.status == "completed"
    first_result = result.trace.turns[0].tool_calls[0]
    assert first_result.is_error
    assert "must not be empty" in first_result.result


def test_all_skip_decisions_complete(tmp_path: Path) -> None:
    client = FakeClient(
        [message(finish({"file": "README.md", "action": "skip", "rationale": "docs"}))]
    )
    result = run_agent(make_runtime(tmp_path, client), "prompt")
    assert result.manifest.status == "completed"
    assert result.manifest.files_written == []


def test_api_failure_is_recorded_as_error(tmp_path: Path) -> None:
    class ExplodingMessages:
        def create(self, **kwargs: Any) -> Any:
            raise RuntimeError("connection reset")

    class ExplodingClient:
        def __init__(self) -> None:
            self.messages = ExplodingMessages()

    runtime = make_runtime(tmp_path, FakeClient([]))
    runtime = AgentRuntime(
        settings=runtime.settings,
        client=cast(AnthropicClient, ExplodingClient()),
        definition=runtime.definition,
        skills=runtime.skills,
        repo_root=runtime.repo_root,
        diff_path=runtime.diff_path,
        out_dir=runtime.out_dir,
        sandbox=runtime.sandbox,
    )
    result = run_agent(runtime, "prompt")
    assert result.manifest.status == "error"
    assert "RuntimeError: connection reset" in result.trace.notes


def test_file_budget_is_enforced(tmp_path: Path) -> None:
    payload = {"path": "backend/tests/test_a.py", "content": "def test_a(): pass\n"}
    second = {"path": "backend/tests/test_b.py", "content": "def test_b(): pass\n"}
    client = FakeClient(
        [
            message(tool_block("write_test_file", payload)),
            message(tool_block("write_test_file", second)),
        ]
    )
    runtime = make_runtime(tmp_path, client, budgets=Budgets(max_files=1))
    result = run_agent(runtime, "prompt")
    assert result.manifest.status == "budget_exceeded"
    assert result.manifest.files_written == ["backend/tests/test_a.py"]
    assert "file limit reached" in result.trace.notes[0]


def test_tools_are_filtered_by_the_definition(tmp_path: Path) -> None:
    allowed = ["get_diff", "activate_skill", "write_test_file", "get_coverage"]
    client = FakeClient([message(finish({"file": "a.py", "action": "skip", "rationale": "docs"}))])
    run_agent(make_runtime(tmp_path, client, tools=allowed), "prompt")
    tool_names = {spec["name"] for spec in client.messages.calls[0]["tools"]}
    assert tool_names == set(allowed) | {"finish"}


def test_parse_decisions_rejects_non_list_and_empty() -> None:
    with pytest.raises(ValueError, match="must be a list"):
        parse_decisions({"decisions": "nope"})
    with pytest.raises(ValueError, match="must not be empty"):
        parse_decisions({"decisions": []})
