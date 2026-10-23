# Sandbox

The sandbox executes untrusted code (the PR's source and tests, plus any test
the model writes) with no network, no secrets, a read-only repository mount, a
non-root user and resource limits.

## Usage

```sh
# Backend tests with coverage
ai_test_agent/sandbox/run.sh --stack backend --repo . --out /tmp/be --mode coverage

# Frontend tests with coverage
ai_test_agent/sandbox/run.sh --stack frontend --repo . --out /tmp/fe --mode coverage

# A subset, with extra arguments passed through
ai_test_agent/sandbox/run.sh --stack backend --repo . -- \
  tests/features/todos/test_repository.py -q
```

Coverage reports are written to the `--out` directory
(`be_coverage.json`, `fe_coverage/`). The directory is created if needed and
made world-writable because the container runs as uid 65534.

The image is built on demand from the repository root, using the application's
own lock files at the **trusted base revision**:

```sh
docker build -t taskly-sandbox:local -f ai_test_agent/sandbox/Dockerfile .
```

## What the container gets

| Control          | Value                                                        |
| ---------------- | ------------------------------------------------------------ |
| Network          | `--network none`                                             |
| Filesystem       | `--read-only` root, repo mounted `:ro`, tmpfs at `/tmp`      |
| User             | `65534:65534`, `--cap-drop ALL`                              |
| Privileges       | `--security-opt no-new-privileges`                           |
| Limits           | 512 pids, 2 GiB memory, 2 CPUs                               |
| Environment      | explicit allowlist only; never `ANTHROPIC_API_KEY` or tokens |

The Docker CLI itself runs under `env -i` so the caller's environment (including
an API key used for local runs) is not inherited by the client.

## Pitfalls found while building this

1. **Read-only mounts and coverage.** `coverage.py` and Vitest both want to
   write next to the project. Running with `--cov-report=json:/tmp/...` and
   `--coverage.reportsDirectory=/out/...` still failed for Vitest because Vite
   writes its transform cache into `node_modules/.vite`. The entrypoint copies
   the checkout into `/tmp/work` (tmpfs) and the frontend's `node_modules` from
   `/opt/frontend`, so every write lands in the disposable tmpfs. The repository
   mount is never written to.
2. **Vitest 4 removed `--cacheDir`.** The flag now fails with a CAC error.
   Redirecting the cache is not needed once `node_modules` is writable.
3. **`npm ci --ignore-scripts`.** Verified against this lock file: esbuild and
   rollup resolve their platform binaries through optional dependencies, so the
   frontend suite still runs. Scripts stay disabled at install time.
4. **Backend working directory.** `pytest` must run with `cwd=backend` or
   `backend/pyproject.toml` (and its coverage omits) is not picked up. The
   entrypoint `cd`s into the stack directory before exec.
5. **pytest cache.** `-p no:cacheprovider -o cache_dir=/tmp/pytest_cache` keeps
   pytest from trying to write `.pytest_cache` next to the read-only sources.
6. **Node in the Python image.** Node is copied from the digest-pinned
   `node:22-bookworm-slim` stage into the digest-pinned `python:3.12-slim`
   stage. No extra apt packages are required.
7. **Coverage output ownership.** The bind-mounted output directory is created
   by the caller; uid 65534 needs write access, hence `chmod 0777`.

The same container is used by the agent's `run_pytest`/`run_vitest` tools, by
the verifier and by the workflows. There is no second execution path.
