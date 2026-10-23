# syntax=docker/dockerfile:1.7

# Node is taken from the official image so the sandbox can run the frontend
# suite without provisioning a second runtime.
FROM node:22-bookworm-slim@sha256:de170b39439eb0e5a3444ad7d60b015614a381e10fecae2e30ec9e735122f38d AS node

FROM python:3.12-slim-bookworm@sha256:6a0e06f5ba0b373d051aabd3fffb9b873f27f9a2a3a14bcbe37dee6f0e3bbc70 AS runtime

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

# Application dependencies, installed from the application's own lock files as
# they exist at the trusted base revision. Nothing here comes from the PR.
# hadolint ignore=DL3013
RUN --mount=type=bind,source=backend/requirements.txt,target=/tmp/backend-requirements.txt \
    python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/backend-requirements.txt

COPY frontend/package.json frontend/package-lock.json /opt/frontend/
WORKDIR /opt/frontend
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force

COPY ai_test_agent/sandbox/entrypoint.sh /usr/local/bin/sandbox-entrypoint
RUN chmod 0555 /usr/local/bin/sandbox-entrypoint

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    COVERAGE_FILE=/tmp/.coverage \
    RUFF_CACHE_DIR=/tmp/.ruff_cache \
    NODE_ENV=test \
    CI=true \
    npm_config_cache=/tmp/.npm

WORKDIR /workspace
USER 65534:65534

ENTRYPOINT ["/usr/local/bin/sandbox-entrypoint"]
