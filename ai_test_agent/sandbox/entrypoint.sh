#!/bin/sh
# Prepare a disposable, writable working copy inside /tmp and run one stack.
#
# /workspace is mounted read-only, so nothing here can modify the caller's
# checkout. Dependencies are baked into the image from the trusted base
# revision's lock files; the frontend's node_modules is copied into the tmpfs
# copy because Vite writes its cache under node_modules/.vite.
set -eu

if [ "$#" -lt 2 ]; then
    echo "usage: sandbox-entrypoint <backend|frontend> <command> [args...]" >&2
    exit 2
fi

stack="$1"
shift

case "$stack" in
    backend | frontend) ;;
    *)
        echo "unsupported stack: $stack" >&2
        exit 2
        ;;
esac

work=/tmp/work
mkdir -p "$work"

# Copy only what the tests need. Local virtualenvs and installed node_modules
# from the host are excluded and replaced with the image's trusted copies.
tar -C /workspace -cf - \
    --exclude='backend/.venv' \
    --exclude='backend/coverage' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/coverage' \
    --exclude='frontend/dist' \
    backend frontend | tar -C "$work" -xf -

if [ "$stack" = "frontend" ]; then
    cp -a /opt/frontend/node_modules "$work/frontend/node_modules"
fi

cd "$work/$stack"
exec "$@"
