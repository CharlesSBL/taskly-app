from __future__ import annotations

import re
import sys
from collections.abc import Iterable
from pathlib import Path

USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<ref>[^\s#]+)")
FULL_SHA = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")
# Relative paths and docker references are resolved differently.
LOCAL_PREFIXES = ("./", "docker://")


def check_file(path: Path) -> list[str]:
    """Return one problem string per unpinned `uses:` reference in a workflow."""
    problems: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = USES_PATTERN.match(line)
        if match is None:
            continue
        ref = match.group("ref").strip("\"'")
        if ref.startswith(LOCAL_PREFIXES):
            continue
        if not FULL_SHA.match(ref):
            problems.append(f"{path}:{number}: not pinned to a commit SHA: {ref}")
    return problems


def check_paths(paths: Iterable[Path]) -> list[str]:
    problems: list[str] = []
    for path in paths:
        if path.is_file():
            files = [path]
        else:
            files = sorted(path.rglob("*.yml")) + sorted(path.rglob("*.yaml"))
        for workflow in files:
            problems.extend(check_file(workflow))
    return problems


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    roots = [Path(arg) for arg in arguments] or [Path(".github/workflows"), Path(".github/actions")]
    problems = check_paths(roots)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
