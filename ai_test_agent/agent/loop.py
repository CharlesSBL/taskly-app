"""The custom tool-use loop.

No orchestration framework: the loop is small enough to audit, and every API
message, tool call and token count is recorded in the trace.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from pydantic import ValidationError

from .budget import BudgetExceeded, BudgetGuard, CostMeter, parse_usage
from .config import Settings
from .definition import AgentDefinition
from .manifest import Baseline, Decision, Manifest, ManifestStatus, Stack
from .prompts import build_system_prompt
from .skills import SkillLibrary
from .tools import ToolContext, build_tool_specs, execute
from .tools.execution import SandboxRunner
from .tracing import Trace


class MessagesAPI(Protocol):
    def create(self, **kwargs: Any) -> Any: ...


class AnthropicClient(Protocol):
    messages: MessagesAPI


@dataclass(frozen=True)
class AgentRuntime:
    settings: Settings
    client: AnthropicClient
    definition: AgentDefinition
    skills: SkillLibrary
    repo_root: Path
    diff_path: Path
    out_dir: Path
    sandbox: SandboxRunner
    lockfile_changed: bool = False
    baseline: dict[Stack, Baseline] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    manifest: Manifest
    trace: Trace


def finish_tool_spec() -> dict[str, Any]:
    return {
        "name": "finish",
        "description": (
            "Finish the run and submit one decision per changed file. "
            "Required after the tests and the quality review are complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "array",
                    "items": Decision.model_json_schema(),
                }
            },
            "required": ["decisions"],
        },
    }


def parse_decisions(arguments: dict[str, Any]) -> list[Decision]:
    raw = arguments.get("decisions")
    if not isinstance(raw, list):
        raise ValueError("decisions must be a list")
    if not raw:
        raise ValueError("decisions must not be empty")
    return [Decision.model_validate(item) for item in raw]


def _text_of(content: list[Any]) -> str:
    parts = [
        block.text
        for block in content
        if getattr(block, "type", None) == "text" and isinstance(getattr(block, "text", None), str)
    ]
    return "\n".join(parts)


def run_agent(runtime: AgentRuntime, user_prompt: str) -> AgentResult:
    settings = runtime.settings
    trace = Trace(model=settings.model)
    meter = CostMeter(price=settings.price)
    guard = BudgetGuard(budgets=settings.budgets)
    context = ToolContext(
        repo_root=runtime.repo_root,
        diff_path=runtime.diff_path,
        out_dir=runtime.out_dir,
        guard=guard,
        sandbox=runtime.sandbox,
        skills=runtime.skills,
        trace=trace,
        lockfile_changed=runtime.lockfile_changed,
        baseline=runtime.baseline,
        max_diff_bytes=settings.budgets.max_diff_bytes,
    )

    allowed = set(runtime.definition.tools) - {"finish"}
    tools = [spec for spec in build_tool_specs(runtime.skills) if spec["name"] in allowed]
    tools.append(finish_tool_spec())

    system_prompt = build_system_prompt(runtime.definition, settings, runtime.skills)
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]

    status: ManifestStatus = "error"
    finished = False
    notes: list[str] = []

    try:
        for turn_index in range(1, settings.budgets.max_turns + 1):
            guard.start_turn()
            response = runtime.client.messages.create(
                model=settings.model,
                max_tokens=settings.budgets.max_output_tokens,
                system=system_prompt,
                messages=messages,
                tools=tools,
            )
            meter.add(parse_usage(getattr(response, "usage", None)))
            trace.usage = meter.usage
            trace.cost_usd = float(meter.total_usd)
            guard.charge(meter.total_usd)

            content = list(getattr(response, "content", None) or [])
            turn = trace.start_turn(
                turn_index, getattr(response, "stop_reason", None), _text_of(content)
            )
            messages.append({"role": "assistant", "content": content})

            tool_uses = [block for block in content if getattr(block, "type", None) == "tool_use"]
            if not tool_uses:
                notes.append("model stopped without calling finish")
                break

            results: list[dict[str, Any]] = []
            for block in tool_uses:
                name = str(getattr(block, "name", ""))
                raw_arguments = getattr(block, "input", {}) or {}
                arguments: dict[str, Any] = raw_arguments if isinstance(raw_arguments, dict) else {}
                tool_id = str(getattr(block, "id", ""))
                if name == "finish":
                    try:
                        context.decisions = parse_decisions(arguments)
                    except (ValidationError, ValueError) as exc:
                        result = f"ERROR: invalid finish payload: {exc}"
                        is_error = True
                    else:
                        result = f"recorded {len(context.decisions)} decisions"
                        is_error = False
                        finished = True
                else:
                    result = execute(context, name, arguments)
                    is_error = result.startswith("ERROR:")

                trace.record_tool(turn, name, arguments, result, error=is_error)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result,
                        "is_error": is_error,
                    }
                )
                if finished:
                    break

            messages.append({"role": "user", "content": results})
            if finished:
                status = "completed"
                break
        else:
            notes.append("turn limit reached before finish")
            status = "budget_exceeded"
    except BudgetExceeded as exc:
        notes.append(exc.reason)
        status = "budget_exceeded"
    except Exception as exc:
        # Record API, network and unexpected failures without ever logging the key.
        notes.append(f"{type(exc).__name__}: {exc}")
        status = "error"

    trace.notes.extend(notes)
    manifest = Manifest(
        status=status,
        model=settings.model,
        decisions=context.decisions,
        files_written=context.written,
        skills_used=list(dict.fromkeys(trace.skills_activated)),
        turns=guard.turns,
        input_tokens=meter.usage.input_tokens,
        output_tokens=meter.usage.output_tokens,
        cost_usd=round(float(meter.total_usd), 6),
        lockfile_changed=runtime.lockfile_changed,
        baseline=runtime.baseline,
    )
    return AgentResult(manifest=manifest, trace=trace)
