# Engineering notes

Supporting detail for `SOLUTION.md`: the security controls, the defects the
live runs exposed, what was cut, and the verification that was done locally.

## What the live runs changed

The runs were not only demos: each failure produced a tooling fix, a regression
test and a line in the table below.

| Defect the run exposed | Fix | Regression test |
| --- | --- | --- |
| The sandbox received `backend/...` although it runs with `cwd=backend`, so zero tests were collected | strip the stack prefix in `_run` (`80199c8`) | `test_tools.py::test_run_tools_pass_stack_relative_paths_to_the_sandbox` |
| `run_pytest` rejected `backend/tests`, so the agent verified single files | accept a directory inside the test roots (`c67ca67`) | `test_tools.py::test_run_tools_accept_a_test_directory` |
| A wrong first draft could not be rewritten in the same run | allow rewrites, charge the first write only (`eb50240`) | `test_tools.py::test_write_can_rewrite_the_same_file_without_charging_the_budget` |
| A rewrite loop could spend the whole budget on one file | per-file write cap of 3 | `test_tools.py::test_write_is_capped_per_file` |
| A backend line over the gate's 100 characters reverted a stack | reject at write time, single constant in `lint_policy.py` (`edb4676`) | `test_tools.py::test_write_rejects_a_backend_line_longer_than_the_lint_limit` |
| The gate did not run Prettier, so unformatted files reached `main` | run `tsc` and `prettier --check` on the generated files (`30e7c21`) | `test_gate.py` frontend typecheck test, `run_lint` tool tests |
| The full suite could fail without reverting the stack | require the coverage run to succeed (`30e7c21`) | `test_gate.py::test_failing_full_suite_reverts_the_stack` |
| A closed backfill PR left a stale branch the next run reused | reset the bot branch from the default branch, push with a lease (`7fc1346`) | `test_commit.py::test_force_push_uses_a_lease_on_the_bot_branch` |
| Publisher resolved a relative patch path after `git -C` | resolve before calling git (`9d255c3`) | `test_commit.py::test_relative_patch_path_is_resolved_before_git` |
| A skipped job suppressed the verification gate | `if: always()` on the gate and no conditional dependency (`46a7b34`) | `test_workflows.py::test_verifier_always_runs_after_the_agent_job` |
| Artifact download nested the patch under an extra directory | download at the workspace root (`4c90556`) | `test_workflows.py::test_artifact_downloads_are_not_nested_under_a_path` |
| A truncated provider response looked like a normal stop | explicit note and a larger cap (`4441245`) | `test_loop.py::test_truncated_response_is_reported_and_uses_the_configured_cap` |
| A transient provider error lost the whole run | three retries with backoff, trace always uploaded (`2459d89`) | `test_loop.py::test_transient_api_errors_are_retried` |

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
| Secret scanning | `detect-secrets` on the tree, `gitleaks` over the full history (`.gitleaks.toml`) |

## What was cut, in order

1. Diff-coverage (not implemented).
2. Multiple backfill runs with a hard cumulative ceiling (single run instead).
3. Extra comment states beyond the six implemented.
4. Fail-on-base polish (no automatic flip of a test's status into a revert).

Flakiness rerun is implemented: the accepted tests run twice and a second-run
failure reverts the stack.

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

The full pipeline was also exercised end to end on a scratch clone with a
hand-written candidate test (not agent output): the verifier accepted the
backend stack, the differential check reported `passed on both`, and the
publisher rendered the comment from the real report. That run is only a smoke
test; every number in `SOLUTION.md` comes from the workflow runs linked there.

## Durable evidence

Actions artifacts expire, so one real run is copied into `docs/evidence/`:
the sticky-comment report, the gate's verification report and a trimmed agent
trace from run
[39927537759](https://github.com/CharlesSBL/taskly-app/actions/runs/39927537759).
