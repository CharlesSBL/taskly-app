"""Fail-closed integrity checks for agent output.

The manifest and the patch are untrusted. Path rules are duplicated from the
agent's write policy on purpose: the verifier must not share a permissive bug
with the component it checks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agent.manifest import Manifest

MAX_PATCH_BYTES = 512 * 1024

BACKEND_TEST = re.compile(r"^backend/tests/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py$")
BACKEND_INIT = re.compile(r"^backend/tests/(?:[A-Za-z0-9_]+/)*__init__\.py$")
FRONTEND_TEST = re.compile(
    r"^frontend/src/(?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+\.test\.(?:ts|tsx)$"
)
TOOLING_PREFIXES = ("ai_test_agent/", ".github/", ".claude/", "sandbox/")
FORBIDDEN_NAMES = {
    "conftest.py",
    "pytest.ini",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
}


@dataclass(frozen=True)
class IntegrityResult:
    ok: bool
    violations: list[str]
    paths: list[str]

    def as_dict(self) -> dict[str, object]:
        return {"ok": self.ok, "violations": list(self.violations), "paths": list(self.paths)}


def is_allowed_test_path(path: str) -> bool:
    return bool(
        BACKEND_TEST.fullmatch(path)
        or BACKEND_INIT.fullmatch(path)
        or FRONTEND_TEST.fullmatch(path)
    )


def path_violation(path: str) -> str | None:
    if not path:
        return "empty path"
    if path.startswith("/") or "\\" in path or "\x00" in path:
        return f"unsafe path: {path!r}"
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        return f"path traversal or empty segment: {path!r}"
    if path.startswith(TOOLING_PREFIXES):
        return f"tooling path is out of scope: {path}"
    if parts[-1] in FORBIDDEN_NAMES:
        return f"forbidden file: {path}"
    if not is_allowed_test_path(path):
        return f"path outside the test allowlist: {path}"
    return None


def patch_paths(patch: str) -> list[str]:
    """Extract target paths from a unified diff."""
    paths: list[str] = []
    for line in patch.splitlines():
        if line.startswith("+++ b/"):
            paths.append(line[len("+++ b/") :])
        elif line.startswith("+++ /dev/null"):
            paths.append("")
    return paths


def check_patch(patch: str, manifest: Manifest) -> IntegrityResult:
    violations: list[str] = []
    if len(patch.encode("utf-8")) > MAX_PATCH_BYTES:
        violations.append(f"patch exceeds {MAX_PATCH_BYTES} bytes")

    if "GIT binary patch" in patch:
        violations.append("binary patches are not allowed")
    if "new file mode 120000" in patch or "new mode 120000" in patch:
        violations.append("symlink patches are not allowed")
    if "rename from " in patch or "rename to " in patch or "deleted file mode" in patch:
        violations.append("renames and deletions are not allowed")

    for line in patch.splitlines():
        if line.startswith(('+++ b/"', '--- a/"')):
            violations.append("quoted patch paths are not allowed")

    paths = patch_paths(patch)
    for path in paths:
        problem = path_violation(path)
        if problem:
            violations.append(problem)

    declared = set(manifest.files_written)
    actual = set(paths)
    if declared != actual:
        missing = sorted(declared - actual)
        extra = sorted(actual - declared)
        if missing:
            violations.append(f"manifest lists files missing from the patch: {missing}")
        if extra:
            violations.append(f"patch contains undeclared files: {extra}")

    for decision in manifest.decisions:
        if decision.action == "skip":
            continue
        target = decision.target_test_file
        if target is None:
            violations.append(f"decision for {decision.file} has no target_test_file")
            continue
        problem = path_violation(target)
        if problem:
            violations.append(f"invalid target_test_file: {problem}")

    return IntegrityResult(ok=not violations, violations=violations, paths=sorted(paths))
