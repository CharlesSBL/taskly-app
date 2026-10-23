"""Command line entry point: `python -m agent --mode pr|backfill ...`.

The same code path is used by the workflows and by local runs. There is no
second gate: the verifier always re-checks what this produces.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import cast

import anthropic

from .config import ConfigError, Settings
from .definition import DefinitionError, load_agent_definition
from .loop import AgentRuntime, AnthropicClient, run_agent
from .manifest import Baseline, Stack
from .patch import build_candidate_patch
from .prompts import build_user_prompt
from .skills import SkillError, SkillLibrary
from .tools import build_tool_specs
from .tools.execution import SubprocessSandbox

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _load_baseline(path: Path | None) -> dict[Stack, Baseline]:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("baseline JSON must be an object keyed by stack")
    baseline: dict[Stack, Baseline] = {}
    for stack in ("backend", "frontend"):
        if stack in raw:
            baseline[stack] = Baseline.model_validate(raw[stack])
    return baseline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m agent")
    parser.add_argument("--mode", choices=["pr", "backfill"], default="pr")
    parser.add_argument("--repo", type=Path, required=True, help="checkout under test")
    parser.add_argument("--diff", type=Path, required=True, help="path to the PR diff")
    parser.add_argument("--out", type=Path, required=True, help="artifact directory")
    parser.add_argument("--skills-dir", type=Path)
    parser.add_argument("--agent-definition", type=Path)
    parser.add_argument("--sandbox-script", type=Path)
    parser.add_argument("--changed-files", default="")
    parser.add_argument("--backfill-files", default="")
    parser.add_argument("--baseline-json", type=Path)
    parser.add_argument("--lockfile-changed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        settings = Settings.from_env(args.mode)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    api_key = os.environ.get(settings.api_key_env, "")
    if not api_key:
        print(f"{settings.api_key_env} is not set", file=sys.stderr)
        return 2

    skills_dir = args.skills_dir or (PACKAGE_ROOT.parent / ".claude" / "skills")
    agent_path = args.agent_definition or (skills_dir.parent / "agents" / "unit-test-agent.md")
    sandbox_script = args.sandbox_script or (PACKAGE_ROOT / "sandbox" / "run.sh")

    try:
        skills = SkillLibrary.discover(skills_dir)
        known_tools = {spec["name"] for spec in build_tool_specs(skills)} | {"finish"}
        definition = load_agent_definition(agent_path, known_tools)
        baseline = _load_baseline(args.baseline_json)
    except (ConfigError, DefinitionError, SkillError, ValueError) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    if definition.model not in ("default", settings.model):
        print(
            f"agent definition pins {definition.model!r} but config uses {settings.model!r}",
            file=sys.stderr,
        )
        return 2

    args.out.mkdir(parents=True, exist_ok=True)
    client = (
        anthropic.Anthropic(api_key=api_key, base_url=settings.base_url)
        if settings.base_url
        else anthropic.Anthropic(api_key=api_key)
    )
    runtime = AgentRuntime(
        settings=settings,
        client=cast(AnthropicClient, client),
        definition=definition,
        skills=skills,
        repo_root=args.repo.resolve(),
        diff_path=args.diff.resolve(),
        out_dir=args.out.resolve(),
        sandbox=SubprocessSandbox(
            repo_root=args.repo.resolve(),
            script=sandbox_script.resolve(),
            out_dir=args.out.resolve(),
        ),
        lockfile_changed=args.lockfile_changed,
        baseline=baseline,
    )
    user_prompt = build_user_prompt(
        mode=args.mode,
        changed_files=_split(args.changed_files),
        baseline=baseline,
        lockfile_changed=args.lockfile_changed,
        backfill_targets=_split(args.backfill_files),
    )

    result = run_agent(runtime, user_prompt)
    result.manifest.write(args.out / "agent_manifest.json")
    result.trace.write(args.out / "agent_trace.json")
    build_candidate_patch(
        runtime.repo_root,
        result.manifest.files_written,
        args.out / "candidate_tests.patch",
    )

    print(
        json.dumps(
            {
                "status": result.manifest.status,
                "decisions": len(result.manifest.decisions),
                "files_written": result.manifest.files_written,
                "cost_usd": result.manifest.cost_usd,
                "turns": result.manifest.turns,
            },
            indent=2,
        )
    )
    return 1 if result.manifest.status == "error" else 0
