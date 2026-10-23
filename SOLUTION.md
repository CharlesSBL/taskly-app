# Taskly with an AI unit-test agent

This repository adds a custom agent that analyzes a pull request, writes or
updates unit tests for the Taskly backend and frontend, and proves the tests
through a sandboxed verification gate before a human can commit them.

- Agent + skills: `.claude/agents/unit-test-agent.md`, `.claude/skills/`
- Runtime: `ai_test_agent/` (`agent`, `verifier`, `publisher`, `sandbox`,
  `selftests`)
- Workflows: `.github/workflows/unit-test-agent.yml` (PR) and
  `coverage-backfill.yml` (manual backfill)

## Architecture

```mermaid
flowchart LR
  subgraph PR["Pull request (untrusted data)"]
    head["head SHA"]
  end
  subgraph T["Trusted checkout: base SHA"]
    agent["agent/<br/>tool-use loop"]
    skills[".claude/skills"]
    verifier["verifier/"]
    publisher["publisher/"]
    sandbox["sandbox/run.sh"]
  end
  subgraph Jobs["Workflow jobs"]
    j1["1. agent-run<br/>API key in one step only"]
    j2["2. verify-gate<br/>no secrets"]
    j3["3. publish-results<br/>comment only"]
    j4["commit-approved<br/>opt-in, contents: write"]
  end
  head -->|diff + files, read-only| j1
  agent --> j1
  skills --> agent
  j1 -->|untrusted artifact| j2
  verifier --> j2
  sandbox --> j2
  j2 -->|verified patch + sha256| j3
  j2 -->|verified patch + sha256| j4
  publisher --> j4
```

## Decisions

| Decision | Rationale | Trade-off |
| --- | --- | --- |
| Custom tool-use loop on the official `anthropic` SDK | Every API call, tool call and token count is auditable; no framework hides the control flow | We own retries and message plumbing |
| Provider abstraction: Anthropic and DeepSeek | DeepSeek exposes an Anthropic-compatible Messages API, so the same SDK, tools and loop work unchanged; the key, base URL, default model and price table are selected in one place | A second price table to maintain, and DeepSeek peak rates are used for budgets |
| Direct SDK instead of LangGraph or similar | Fewer dependencies, clearer security boundary, nothing to keep in sync with the model API | No framework features (persistence, graph visualization) |
| All tooling runs from the trusted base checkout | The PR cannot change the code that holds the key or makes decisions | Tooling changes need their own PR before a demo PR |
| Patch posted by default, commit opt-in via label | The patch is reviewable and a human decides what lands | A second action is required to commit |
| Per-stack baseline and per-stack revert | A broken backend baseline must not block a healthy frontend | More sandbox runs per PR |
| Differential fail-on-base signal | Shows whether the new tests actually exercise changed behavior | It is evidence, not proof; new source files are `n/a` |
| Strict manifest schema + independent integrity rules | Model output is untrusted and the verifier does not share the agent's path logic | Some duplication between agent and verifier |
| Cost is computed from response usage | No estimates; cache reads/writes are priced separately | Prices must be updated when the model changes |
| Coverage backfill reuses the same gate | One definition of "verified" everywhere | Backfill is serial and slower |

## How to run

Prerequisites:

1. Repository secret `ANTHROPIC_API_KEY`.
2. Actions → General → Workflow permissions: read-only, and "Allow GitHub
   Actions to create and approve pull requests" enabled.
3. Label `ai-tests:commit`.

Pull request flow: open, push to, reopen or label a PR. Add
`ai-tests:commit` only after reviewing the sticky comment; the label event
does not re-run the agent.

Backfill: Actions → Coverage backfill → Run workflow, choose `stack` and
`max_batches`. It updates `chore/ai-backfill-unit-tests` and opens or updates
a PR against the default branch.

Local run (same gate):

```sh
cd ai_test_agent
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
export TASKLY_AGENT_PROVIDER=deepseek   # or anthropic, the default
export DEEPSEEK_API_KEY=...             # ANTHROPIC_API_KEY for Anthropic
.venv/bin/python -m agent --mode pr \
  --repo ../pr --diff ../pr.diff --out ../artifacts \
  --skills-dir ../.claude/skills \
  --agent-definition ../.claude/agents/unit-test-agent.md \
  --sandbox-script sandbox/run.sh
.venv/bin/python -m verifier --verify-only \
  --pr-dir ../pr --trusted-dir .. --base-sha "$(git rev-parse HEAD)" \
  --manifest ../artifacts/agent_manifest.json \
  --patch ../artifacts/candidate_tests.patch --out ../verified
```

## How the agent and skills load

`agent/definition.py` reads `.claude/agents/unit-test-agent.md`: the
frontmatter declares name, description, model key and allowed tools, the body
becomes the system prompt. `agent/skills.py` reads
`.claude/skills/*/SKILL.md`; only name and description are in the prompt until
the model calls `activate_skill`, which returns the body and records the
activation in the trace.

## Example run

<!-- TODO: replace with the real agent run after ANTHROPIC_API_KEY is set. -->

## Security checklist

| Control | How it is enforced |
| --- | --- |
| Trusted checkout for key-holding and gate code | Jobs 1–3 checkout the base SHA into `trusted/`; the head is a separate `pr/` tree |
| Least privilege | `permissions: {}` at workflow level; per-job read; commit job only has `contents: write` |
| API keys only in the agent step | `env:` on that single step; verifier/publisher jobs have no secrets; the provider key is read from config |
| `pull_request`, not `pull_request_target` | Workflow trigger; forks are skipped with a step summary |
| Untrusted diff/files and model output | `<untrusted_source_data>` wrapping, escaped closing tag, strict schemas, independent verifier allowlists |
| Lockfile changes | Dependencies always come from the base revision's lock files; the report warns when the PR changed them |
| Labeler authorization | `gh api .../collaborators/{login}/permission`; only `admin` or `write` |
| Same-repo only for commit | `head.repo.full_name == github.repository` |
| Action pinning | Every `uses:` is a 40-character SHA; `verifier.action_pins` fails the build otherwise |
| Dependabot | actions, pip (`/ai_test_agent`), npm (`/frontend`) |
| Sandbox | no network, read-only mounts, non-root, caps dropped, resource limits, tmpfs |
| Cost and loop control | `max_turns`, `max_files`, `max_diff_bytes`, `$0.75`/`$5.00` ceilings, concurrency per PR, bot guard, label events never re-run the agent |
| Fail on base | Worktree of the base SHA, per-file `true`/`false`/`n/a` |
| Patch integrity | sha256 re-checked twice (verifier output and publisher), allowlist and `git apply --numstat` agreement |
| No artifact code execution in the publisher | Publisher only reads the patch and report |
| Redaction | Trace writer redacts credentials recursively and truncates fields |
| Fail closed | Unknown model, malformed manifest, unreadable permission or bad sha all stop |

## Assumptions

- The base revision is a git checkout with the PR's base commit available.
- The repository uses `main` by default.
- Backend tests run with `cwd=backend`; frontend tests with `cwd=frontend`.
- The provider is `anthropic` by default; this repository is configured with
  `AGENT_PROVIDER=deepseek` and `AGENT_MODEL=deepseek-flash` for testing.
  Prices for both providers were verified on 2026-10-23; DeepSeek budgets use
  the higher peak-hour rates.
- The app's lock file is not hash-pinned, so the sandbox uses binary wheels
  only; the tooling's own lock file is hash-pinned.

## Limitations

- Prompt injection cannot be eliminated. Wrapping, path allowlists and the
  gate reduce impact; they do not make the model trustworthy.
- Fail-on-base is a heuristic: a test can pass on both revisions and still be
  useful, and a test that fails on base may fail for an unrelated reason.
- A PR can edit `.github/workflows/`. Branch protection/CODEOWNERS on tooling
  paths is required before using the commit label on a sensitive repo.
- Forks are skipped; there is no fork execution path.
- Pushes made with `GITHUB_TOKEN` do not trigger workflows, so required checks
  will not re-run on the commit created by the label path. That is why commit
  is opt-in and the patch is the default.
- Model output is non-deterministic; the gate is the stable contract.
- DeepSeek prices differ between peak and off-peak hours; costs are estimated
  at peak rates, so the reported figure is an upper bound outside peak hours.
- Backfill selects at most `3 × max_batches` modules in one agent run with a
  single $5 ceiling, rather than several independent runs.
- Diff coverage is not computed.
- The TypeScript quality checks are lexical heuristics, not a full parser.
- Coverage deltas depend on the full suite, so pre-existing flaky app tests can
  affect them.

## What was cut, in order

1. Diff-coverage (not implemented).
2. Multiple backfill runs with a hard cumulative ceiling (single run instead).
3. Extra comment states beyond the six implemented.
4. Fail-on-base polish (no automatic flip of a test's status into a revert).

Flakiness rerun is implemented: the accepted tests run twice and a second-run
failure reverts the stack.

## Production changes

- A GitHub App instead of `GITHUB_TOKEN`, so commits can trigger workflows.
- Ephemeral runners or gVisor/Firecracker for stronger isolation.
- Real mutation testing instead of the AST heuristics.
- A cost dashboard and per-repository budgets.
- A golden-PR evaluation suite to measure the agent before changing prompts.
- Org policy and required CODEOWNERS reviews on tooling paths.

## Suppressions

- None in `agent/`, `verifier/`, `publisher/` (no `# noqa`, `# nosec` or
  `eslint-disable`).
- `ai_test_agent/sandbox/Dockerfile`: `# hadolint ignore=DL3013` — pip
  versions come from the application's trusted requirements file.
- Test fixtures that intentionally contain fake credentials are marked
  `# pragma: allowlist secret` so the secret scanner does not flag them.
- `frontend/coverage/**` contains generated files with `eslint-disable`; the
  directory is git-ignored.

## Local verification performed

The full pipeline was exercised end to end on a scratch clone with a
hand-written candidate test (not agent output): verifier accepted the backend
stack, coverage moved 42.0% → 49.7%, the differential check reported
`passed on both`, and the publisher rendered the comment from the real report.
The agent-generated run is recorded in the real PR and in the example section
above once the secret is configured.
