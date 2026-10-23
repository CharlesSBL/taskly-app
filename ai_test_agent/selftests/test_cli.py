from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from agent.cli import _load_baseline, _split, main
from agent.definition import REQUIRED_TOOLS
from agent.manifest import load_manifest


class FakeMessages:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[Any]) -> None:
        self.messages = FakeMessages(responses)


def message(*blocks: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        content=list(blocks),
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )


def tool_block(name: str, arguments: dict[str, Any]) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id="tool-1", name=name, input=arguments)


def make_workspace(tmp_path: Path, model: str = "default") -> tuple[Path, Path, Path]:
    repo = tmp_path / "repo"
    (repo / "backend/app").mkdir(parents=True)
    (repo / "backend/tests").mkdir(parents=True)
    (repo / "backend/app/feature.py").write_text("def add(a, b):\n    return a + b\n")
    diff = "diff --git a/backend/app/feature.py b/backend/app/feature.py\n"
    (tmp_path / "pr.diff").write_text(diff)

    skills = tmp_path / "skills"
    skill_dir = skills / "analyze-diff"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: analyze-diff\ndescription: Analyze\n---\nRead the diff.\n"
    )

    tools = "\n".join(f"  - {tool}" for tool in sorted(REQUIRED_TOOLS))
    definition = tmp_path / "agent.md"
    definition.write_text(
        f"---\nname: unit-test-agent\ndescription: d\nmodel: {model}\ntools:\n{tools}\n---\n"
        "You write tests.\n"
    )
    return repo, definition, skills


def base_args(tmp_path: Path, repo: Path, definition: Path, skills: Path) -> list[str]:
    return [
        "--repo",
        str(repo),
        "--diff",
        str(tmp_path / "pr.diff"),
        "--out",
        str(tmp_path / "out"),
        "--skills-dir",
        str(skills),
        "--agent-definition",
        str(definition),
        "--changed-files",
        "backend/app/feature.py",
    ]


def test_split_and_baseline_loading(tmp_path: Path) -> None:
    assert _split(" a , b,,c ") == ["a", "b", "c"]
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "backend": {"status": "passed", "tests": 21, "coverage": 42.0},
                "unrelated": {"status": "skipped"},
            }
        )
    )
    loaded = _load_baseline(baseline)
    assert loaded["backend"].tests == 21
    assert "unrelated" not in loaded
    assert _load_baseline(None) == {}


def test_invalid_baseline_json_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text("[]")
    with pytest.raises(ValueError, match="keyed by stack"):
        _load_baseline(path)


def test_missing_api_key_exits_without_calling_the_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    repo, definition, skills = make_workspace(tmp_path)
    assert main(base_args(tmp_path, repo, definition, skills)) == 2
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().err


def test_happy_path_writes_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    repo, definition, skills = make_workspace(tmp_path)
    client = FakeClient(
        [
            message(tool_block("get_diff", {})),
            message(
                tool_block(
                    "finish",
                    {
                        "decisions": [
                            {
                                "file": "backend/app/feature.py",
                                "action": "skip",
                                "rationale": "already covered",
                            }
                        ]
                    },
                )
            ),
        ]
    )
    monkeypatch.setattr("agent.cli.anthropic.Anthropic", lambda **_kwargs: client)

    baseline = tmp_path / "baseline.json"
    baseline.write_text(json.dumps({"backend": {"status": "passed", "tests": 21, "coverage": 42}}))
    args = [*base_args(tmp_path, repo, definition, skills), "--baseline-json", str(baseline)]

    assert main(args) == 0
    out = tmp_path / "out"
    manifest = load_manifest(out / "agent_manifest.json")
    assert manifest.status == "completed"
    assert manifest.decisions[0].action == "skip"
    assert manifest.baseline["backend"].coverage == 42
    assert (out / "agent_trace.json").is_file()
    assert (out / "candidate_tests.patch").read_text() == ""
    assert json.loads(capsys.readouterr().out)["status"] == "completed"


def test_unknown_tool_in_definition_exits_with_configuration_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    repo, definition, _ = make_workspace(tmp_path)
    empty_skills = tmp_path / "empty-skills"
    empty_skills.mkdir()
    assert main(base_args(tmp_path, repo, definition, empty_skills)) == 2
    assert "unknown tools: activate_skill" in capsys.readouterr().err


def test_model_mismatch_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    repo, definition, skills = make_workspace(tmp_path, model="claude-opus-5-5")
    client = FakeClient([])
    monkeypatch.setattr("agent.cli.anthropic.Anthropic", lambda **_kwargs: client)
    assert main(base_args(tmp_path, repo, definition, skills)) == 2
    assert "pins 'claude-opus-5-5'" in capsys.readouterr().err


def test_incomplete_run_returns_one(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    repo, definition, skills = make_workspace(tmp_path)
    client = FakeClient([message(SimpleNamespace(type="text", text="done"))])
    monkeypatch.setattr("agent.cli.anthropic.Anthropic", lambda **_kwargs: client)
    assert main(base_args(tmp_path, repo, definition, skills)) == 1
    manifest = load_manifest(tmp_path / "out" / "agent_manifest.json")
    assert manifest.status == "error"


def test_deepseek_provider_uses_the_anthropic_compatible_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "deepseek")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "dsk-test-key")  # pragma: allowlist secret
    repo, definition, skills = make_workspace(tmp_path)
    client = FakeClient(
        [
            message(
                tool_block(
                    "finish",
                    {"decisions": [{"file": "README.md", "action": "skip", "rationale": "docs"}]},
                )
            )
        ]
    )
    captured: dict[str, Any] = {}

    def fake_anthropic(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return client

    monkeypatch.setattr("agent.cli.anthropic.Anthropic", fake_anthropic)

    assert main(base_args(tmp_path, repo, definition, skills)) == 0
    assert captured["base_url"] == "https://api.deepseek.com/anthropic"
    assert captured["api_key"] == "dsk-test-key"  # pragma: allowlist secret
    manifest = load_manifest(tmp_path / "out" / "agent_manifest.json")
    assert manifest.model == "deepseek-flash"


def test_deepseek_missing_key_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "deepseek")
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    repo, definition, skills = make_workspace(tmp_path)
    assert main(base_args(tmp_path, repo, definition, skills)) == 2
    assert "DEEPSEEK_API_KEY is not set" in capsys.readouterr().err
