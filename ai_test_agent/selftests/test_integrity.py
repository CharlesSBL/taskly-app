from __future__ import annotations

from agent.manifest import Decision, Manifest
from verifier.integrity import check_patch, is_allowed_test_path, patch_paths, path_violation


def manifest_for(files: list[str], decisions: list[Decision] | None = None) -> Manifest:
    return Manifest(
        status="completed",
        model="claude-sonnet-5-5",
        files_written=files,
        decisions=decisions or [],
    )


def patch_for(path: str, *, mode: str = "new file mode 100644") -> str:
    return (
        f"diff --git a/{path} b/{path}\n"
        f"{mode}\n"
        "index 0000000..1111111\n"
        "--- /dev/null\n"
        f"+++ b/{path}\n"
        "@@ -0,0 +1,2 @@\n"
        "+def test_x():\n"
        "+    assert 1 == 1\n"
    )


def test_valid_backend_patch_passes() -> None:
    path = "backend/tests/features/todos/test_router.py"
    result = check_patch(patch_for(path), manifest_for([path]))
    assert result.ok
    assert result.paths == [path]


def test_valid_frontend_patch_passes() -> None:
    path = "frontend/src/features/todos/components/Foo.test.tsx"
    result = check_patch(patch_for(path), manifest_for([path]))
    assert result.ok


def test_patch_paths_extracts_targets() -> None:
    assert patch_paths(patch_for("backend/tests/test_a.py")) == ["backend/tests/test_a.py"]


def test_manifest_and_patch_must_agree() -> None:
    path = "backend/tests/test_a.py"
    result = check_patch(patch_for(path), manifest_for([]))
    assert not result.ok
    assert "undeclared files" in result.violations[0]

    result = check_patch(patch_for(path), manifest_for([path, "backend/tests/test_b.py"]))
    assert not result.ok
    assert "missing from the patch" in result.violations[0]


def test_tooling_and_source_paths_are_rejected() -> None:
    assert not check_patch(
        patch_for(".github/workflows/test_x.py"), manifest_for([".github/workflows/test_x.py"])
    ).ok
    assert not check_patch(
        patch_for("ai_test_agent/agent/tools/test_x.py"),
        manifest_for(["ai_test_agent/agent/tools/test_x.py"]),
    ).ok
    assert not check_patch(
        patch_for("backend/app/test_evil.py"), manifest_for(["backend/app/test_evil.py"])
    ).ok


def test_traversal_absolute_and_forbidden_names_are_rejected() -> None:
    for path in (
        "backend/tests/../../evil.py",
        "/etc/passwd",
        "backend/tests/conftest.py",
        "backend/tests/pyproject.toml",
        'backend/tests/"quoted".py',
    ):
        assert path_violation(path) is not None, path


def test_symlink_binary_rename_and_deletion_are_rejected() -> None:
    path = "backend/tests/test_a.py"
    symlink = patch_for(path, mode="new file mode 120000")
    assert not check_patch(symlink, manifest_for([path])).ok

    binary = patch_for(path) + "GIT binary patch\n"
    assert not check_patch(binary, manifest_for([path])).ok

    renamed = patch_for(path) + f"rename from {path}\nrename to {path}\n"
    assert not check_patch(renamed, manifest_for([path])).ok

    deleted = "diff --git a/x b/x\ndeleted file mode 100644\n--- a/x\n+++ /dev/null\n"
    assert not check_patch(deleted, manifest_for([])).ok


def test_invalid_manifest_targets_are_rejected() -> None:
    decision = Decision(
        file="backend/app/x.py",
        action="create",
        rationale="new logic",
        target_test_file="backend/app/x.py",
    )
    result = check_patch(
        patch_for("backend/tests/test_x.py"), manifest_for(["backend/tests/test_x.py"], [decision])
    )
    assert not result.ok
    assert "invalid target_test_file" in result.violations[0]


def test_oversized_patch_is_rejected() -> None:
    path = "backend/tests/test_a.py"
    patch = patch_for(path) + "+x" * 300_000
    assert not check_patch(patch, manifest_for([path])).ok


def test_allowlist_is_exact() -> None:
    assert is_allowed_test_path("backend/tests/test_a.py")
    assert is_allowed_test_path("backend/tests/features/todos/__init__.py")
    assert is_allowed_test_path("frontend/src/lib/http.test.ts")
    assert not is_allowed_test_path("backend/tests/conftest.py")
    assert not is_allowed_test_path("frontend/src/lib/http.test.js")
