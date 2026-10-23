"""Path rules for every file the agent may read or write.

The PR checkout is untrusted. Writes are limited to test files (and empty
`__init__.py` markers) so the agent can never touch application source, the
tooling, workflows, fixtures or `conftest.py`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lint_policy import MAX_LINE_LENGTH

MAX_TEST_BYTES = 64 * 1024
MAX_READ_BYTES = 24 * 1024
# The verifier runs the same ruff invocation defined in `lint_policy.py`, so a
# longer line is rejected before the agent wastes a run.
MAX_BACKEND_LINE = MAX_LINE_LENGTH

TOOLING_PREFIXES = ("ai_test_agent/", ".github/", ".claude/", "sandbox/")
SECRET_FILE_PATTERNS = (
    re.compile(r"(^|/)\.env(\.|$)"),
    re.compile(r"\.(pem|key|p12|pfx)$", re.IGNORECASE),
    re.compile(r"(^|/)id_(rsa|ed25519)$"),
)

BACKEND_TEST = re.compile(r"^backend/tests/(?:[A-Za-z0-9_]+/)*test_[A-Za-z0-9_]+\.py$")
BACKEND_INIT = re.compile(r"^backend/tests/(?:[A-Za-z0-9_]+/)*__init__\.py$")
BACKEND_TEST_DIR = re.compile(r"^backend/tests(?:/[A-Za-z0-9_]+)*$")
FRONTEND_TEST = re.compile(
    r"^frontend/src/(?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+\.test\.(?:ts|tsx)$"
)
FRONTEND_TEST_DIR = re.compile(r"^frontend/src(?:/[A-Za-z0-9_.\-]+)*$")

FORBIDDEN_NAMES = {
    "conftest.py",
    "pytest.ini",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
}


class PathRejected(ValueError):
    """A path failed the allowlist or containment checks."""


def is_tooling_path(raw: str) -> bool:
    normalized = raw
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.startswith(TOOLING_PREFIXES)


@dataclass(frozen=True)
class PathPolicy:
    repo_root: Path

    def _relative(self, raw: str) -> Path:
        if not isinstance(raw, str) or not raw.strip():
            raise PathRejected("path must be a non-empty string")
        if "\x00" in raw:
            raise PathRejected("path contains a NUL byte")
        candidate = Path(raw)
        if candidate.is_absolute():
            raise PathRejected("absolute paths are not allowed")
        if "\\" in raw:
            raise PathRejected("backslashes are not allowed in paths")
        parts = candidate.parts
        if any(part in ("..", ".") for part in parts):
            raise PathRejected("path traversal is not allowed")
        relative = Path(*parts)
        self._reject_symlinks(relative)
        target = (self.repo_root / relative).resolve()
        if not target.is_relative_to(self.repo_root.resolve()):
            raise PathRejected("path escapes the repository")
        return relative

    def _reject_symlinks(self, relative: Path) -> None:
        current = self.repo_root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise PathRejected(f"symlink components are not allowed: {relative}")

    def check_read(self, raw: str) -> Path:
        relative = self._relative(raw)
        name = str(relative)
        if any(pattern.search(name) for pattern in SECRET_FILE_PATTERNS):
            raise PathRejected("secret-bearing files cannot be read")
        return relative

    def check_test_write(self, raw: str, content: str) -> Path:
        relative = self._relative(raw)
        name = relative.as_posix()

        if relative.name in FORBIDDEN_NAMES:
            raise PathRejected(f"{relative.name} is not writable by the agent")
        if is_tooling_path(name):
            raise PathRejected("tooling paths are out of scope")
        if len(content.encode("utf-8")) > MAX_TEST_BYTES:
            raise PathRejected(f"content exceeds {MAX_TEST_BYTES} bytes")

        if BACKEND_INIT.fullmatch(name):
            if content.strip():
                raise PathRejected("__init__.py files must be empty")
            return relative
        if BACKEND_TEST.fullmatch(name) or FRONTEND_TEST.fullmatch(name):
            if content.strip() == "":
                raise PathRejected("test content must not be empty")
            if BACKEND_TEST.fullmatch(name):
                too_long = [
                    number
                    for number, line in enumerate(content.splitlines(), start=1)
                    if len(line) > MAX_BACKEND_LINE
                ]
                if too_long:
                    raise PathRejected(
                        f"line {too_long[0]} is longer than {MAX_BACKEND_LINE} characters; "
                        "the gate runs ruff with --line-length 100"
                    )
            return relative

        raise PathRejected(
            "only backend/tests/**/test_*.py, empty backend/tests/**/__init__.py "
            "and frontend/src/**/*.test.ts(x) are writable"
        )

    def check_test_file(self, raw: str) -> Path:
        """Validate an existing test path (used for execution filters)."""
        relative = self._relative(raw)
        name = relative.as_posix()
        if BACKEND_TEST.fullmatch(name) or FRONTEND_TEST.fullmatch(name):
            return relative
        raise PathRejected(f"not a test file: {name}")

    def check_test_target(self, raw: str) -> Path:
        """Validate an execution argument: a test file or an existing directory.

        Running the whole suite is the only way to see the real state of the
        stack, and the agent asked for `backend/tests` on its first live
        backfill, so directories inside the test roots are accepted too.
        """
        try:
            return self.check_test_file(raw)
        except PathRejected:
            pass
        relative = self._relative(raw)
        name = relative.as_posix()
        is_test_root = BACKEND_TEST_DIR.fullmatch(name) or FRONTEND_TEST_DIR.fullmatch(name)
        if is_test_root and (self.repo_root / relative).is_dir():
            return relative
        raise PathRejected(f"not a test path: {name}")
