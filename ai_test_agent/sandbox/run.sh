#!/bin/sh
# Run one stack's tests inside the hardened sandbox.
#
# Usage:
#   sandbox/run.sh --stack backend|frontend --repo DIR [--out DIR]
#                  [--mode tests|coverage] [-- <extra test arguments>]
#
# The repository is mounted read-only. Coverage and any extra output go to
# --out (default: a new temporary directory), which is printed on stdout when
# the run succeeds so callers can collect reports.
set -eu

usage() {
    cat >&2 <<'EOF'
usage: run.sh --stack backend|frontend --repo DIR [--out DIR]
              [--mode tests|coverage] [-- <extra test arguments>]
EOF
}

stack=""
repo=""
out=""
mode="tests"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --stack)
            stack="${2:?--stack needs a value}"
            shift 2
            ;;
        --repo)
            repo="${2:?--repo needs a value}"
            shift 2
            ;;
        --out)
            out="${2:?--out needs a value}"
            shift 2
            ;;
        --mode)
            mode="${2:?--mode needs a value}"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done

if [ -z "$stack" ] || [ -z "$repo" ]; then
    usage
    exit 2
fi

case "$stack" in
    backend | frontend) ;;
    *)
        echo "unsupported stack: $stack" >&2
        exit 2
        ;;
esac

case "$mode" in
    tests | coverage | typecheck) ;;
    *)
        echo "unsupported mode: $mode" >&2
        exit 2
        ;;
esac

if [ "$mode" = "typecheck" ] && [ "$stack" != "frontend" ]; then
    echo "typecheck is only available for the frontend" >&2
    exit 2
fi

if [ ! -d "$repo/backend" ] || [ ! -d "$repo/frontend" ]; then
    echo "not a taskly checkout: $repo" >&2
    exit 2
fi

repo=$(cd "$repo" && pwd)
if [ -z "$out" ]; then
    out=$(mktemp -d)
fi
mkdir -p "$out"
out=$(cd "$out" && pwd)
# The container runs as an unprivileged uid, so the output mount must be
# writable by it.
chmod 0777 "$out"

image="${TASKLY_SANDBOX_IMAGE:-taskly-sandbox:local}"
if ! docker image inspect "$image" >/dev/null 2>&1; then
    root=$(cd "$(dirname "$0")/../.." && pwd)
    echo "building sandbox image $image" >&2
    docker build -q -t "$image" -f "$root/ai_test_agent/sandbox/Dockerfile" "$root" >/dev/null
fi

run_container() {
    # env -i keeps the caller's environment (including any API key) out of the
    # Docker client; the container itself only receives the allowlist below.
    env -i PATH=/usr/local/bin:/usr/bin:/bin \
        docker run --rm \
        --network none \
        --read-only \
        --tmpfs /tmp:rw,exec,nosuid,size=1536m \
        --user 65534:65534 \
        --cap-drop ALL \
        --security-opt no-new-privileges \
        --pids-limit 512 \
        --memory 2g \
        --memory-swap 2g \
        --cpus 2 \
        -e PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -e HOME=/tmp \
        -e TMPDIR=/tmp \
        -e COVERAGE_FILE=/tmp/.coverage \
        -e RUFF_CACHE_DIR=/tmp/.ruff_cache \
        -e PYTHONDONTWRITEBYTECODE=1 \
        -e NODE_ENV=test \
        -e CI=true \
        -e npm_config_cache=/tmp/.npm \
        -v "$repo:/workspace:ro" \
        -v "$out:/out:rw" \
        "$image" "$stack" "$@"
}

if [ "$stack" = "backend" ]; then
    if [ "$mode" = "coverage" ]; then
        run_container python -m pytest \
            -p no:cacheprovider \
            -o cache_dir=/tmp/pytest_cache \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=json:/out/be_coverage.json \
            "$@"
    else
        run_container python -m pytest \
            -p no:cacheprovider \
            -o cache_dir=/tmp/pytest_cache \
            "$@"
    fi
else
    if [ "$mode" = "typecheck" ]; then
        run_container npx tsc --noEmit
    elif [ "$mode" = "coverage" ]; then
        run_container npx vitest run \
            --coverage \
            --coverage.reportsDirectory=/out/fe_coverage \
            "$@"
    else
        run_container npx vitest run "$@"
    fi
fi

echo "sandbox output: $out"
