# Security policy

## Supported versions

This repository is a demonstration project. Only the `main` branch is
supported.

## Reporting a vulnerability

Open a private security advisory on GitHub (Security → Advisories → Report a
vulnerability). Do not open a public issue for a suspected secret leak or a
sandbox escape.

## Secrets

- The only secret is `ANTHROPIC_API_KEY`, stored as a GitHub Actions secret.
- It is injected into exactly one step: the agent run in
  `unit-test-agent.yml` / `coverage-backfill.yml`.
- The verifier and publisher jobs run with no secrets.
- Traces are redacted before they are written; the redaction patterns cover
  Anthropic, GitHub, AWS and generic bearer/key-value credentials.
- Never put a key in `.env` and commit it. `.env` is ignored; `.env.example`
  contains only local database defaults.

## Trust model

- All tooling (agent loop, verifier, publisher, sandbox image) runs from a
  checkout of the **base revision**, not from the pull request.
- The pull request head is data. It is read, diffed, and executed only inside
  the sandbox with no network and no secrets.
- Fork pull requests never receive secrets (`pull_request`, not
  `pull_request_target`).
- Changes to `ai_test_agent/`, `.github/`, `.claude/` or `sandbox/` are out of
  scope for the agent; the report shows a notice.
- A pull request can still edit the workflow file. Branch protection and
  CODEOWNERS on `.github/` and `ai_test_agent/` are required before enabling
  the opt-in commit label on a sensitive repository.

## Sandbox

The sandbox (`ai_test_agent/sandbox/`) runs with:

- no network,
- a read-only root and a read-only repository mount,
- uid 65534 and all capabilities dropped,
- `no-new-privileges`,
- CPU, memory and pid limits,
- an explicit environment allowlist (no API key).

Dependencies are installed from the base revision's lock files at image build
time. The checkout is copied into a tmpfs inside the container before tests
run.

## Commit path

The opt-in commit path re-verifies the patch sha256 and the path allowlist in
trusted publisher code and only accepts `admin` or `write` labelers.
