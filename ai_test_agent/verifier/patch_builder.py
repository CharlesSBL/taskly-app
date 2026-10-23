"""Split and rebuild unified diffs per file, and hash the verified patch."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

DIFF_HEADER = re.compile(r"^diff --git a/(?P<path>.+?) b/(?P<target>.+)$")


def split_patch(patch: str) -> list[tuple[str, str]]:
    """Return (path, block) pairs in patch order."""
    blocks: list[tuple[str, str]] = []
    current_path: str | None = None
    current: list[str] = []

    for line in patch.splitlines(keepends=True):
        if line.startswith("diff --git "):
            if current_path is not None:
                blocks.append((current_path, "".join(current)))
            match = DIFF_HEADER.match(line.rstrip("\n"))
            current_path = match.group("target") if match else ""
            current = [line]
        elif current_path is not None:
            current.append(line)

    if current_path is not None:
        blocks.append((current_path, "".join(current)))
    return blocks


def build_patch(patch: str, paths: Iterable[str]) -> str:
    wanted = set(paths)
    parts = [block for path, block in split_patch(patch) if path in wanted]
    return "".join(parts)


def patch_sha256(patch: str) -> str:
    return hashlib.sha256(patch.encode("utf-8")).hexdigest()
