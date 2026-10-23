from __future__ import annotations

from verifier.patch_builder import build_patch, patch_sha256, split_patch


def block(path: str, body: str) -> str:
    return (
        f"diff --git a/{path} b/{path}\nnew file mode 100644\n--- /dev/null\n"
        f"+++ b/{path}\n@@ -0,0 +1 @@\n+{body}\n"
    )


def test_split_and_rebuild() -> None:
    backend = block("backend/tests/test_a.py", "pass")
    frontend = block("frontend/src/a.test.ts", "it('a', () => { expect(1).toBe(1) })")
    patch = backend + frontend

    blocks = split_patch(patch)
    assert [path for path, _ in blocks] == [
        "backend/tests/test_a.py",
        "frontend/src/a.test.ts",
    ]
    assert build_patch(patch, ["frontend/src/a.test.ts"]) == frontend
    assert build_patch(patch, []) == ""


def test_sha256_is_stable() -> None:
    patch = block("backend/tests/test_a.py", "pass")
    assert patch_sha256(patch) == patch_sha256(patch)
    assert len(patch_sha256(patch)) == 64
    assert patch_sha256(patch) != patch_sha256(patch + " ")
    assert patch_sha256("") == patch_sha256("")
