"""Static quality checks for generated tests.

These are heuristics, not a proof: the gate treats them as a first filter and
always runs the tests afterwards. They catch the failure modes the agent is
known to produce (empty assertions, snapshot-only tests, sleeps).
"""

from __future__ import annotations

import ast
import re

from .types import Issue

TRIVIAL_ASSERTIONS = {"True", "1", "1.0"}
TEST_BLOCK = re.compile(r"\b(?:it|test)\s*\(\s*(['\"`])(?P<name>.*?)\1\s*,")
SKIP_MARKERS = ("pytest.mark.skip", "unittest.skip", "pytest.skip")


def _dotted(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _is_trivial_assertion(node: ast.expr) -> bool:
    if isinstance(node, ast.Constant):
        return bool(node.value)
    return bool(isinstance(node, ast.Name) and node.id in TRIVIAL_ASSERTIONS)


def _has_real_assertion(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(function):
        if isinstance(node, ast.Assert) and not _is_trivial_assertion(node.test):
            return True
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name.endswith(("assert_called", "assert_called_once", "assert_called_with")):
                return True
            if name.endswith(("assert_called_once_with", "assert_not_called", "assert_any_call")):
                return True
            if name.startswith("self.assert"):
                return True
            if "raises" in name:
                return True
        if isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call) and "raises" in _dotted(
                    item.context_expr.func
                ):
                    return True
    return False


def _skip_decorators(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        _dotted(decorator.func if isinstance(decorator, ast.Call) else decorator).startswith(
            SKIP_MARKERS
        )
        for decorator in function.decorator_list
    )


def check_python_source(path: str, source: str) -> list[Issue]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [Issue(path, f"syntax error: {exc.msg}", exc.lineno)]

    issues: list[Issue] = []
    tests = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not tests:
        issues.append(Issue(path, "no test functions found"))

    for function in tests:
        if _skip_decorators(function):
            issues.append(Issue(path, f"{function.name} is skipped", function.lineno))
        if not _has_real_assertion(function):
            issues.append(Issue(path, f"{function.name} has no real assertion", function.lineno))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert) and _is_trivial_assertion(node.test):
            issues.append(Issue(path, "trivial assertion", node.lineno))
        if isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name == "time.sleep":
                issues.append(
                    Issue(path, "time.sleep makes the test non-deterministic", node.lineno)
                )
            if name in {"pytest.skip", "unittest.skip"}:
                issues.append(Issue(path, "unconditional skip", node.lineno))
    return issues


def _test_blocks(source: str) -> list[tuple[str, int]]:
    blocks: list[tuple[str, int]] = []
    for match in TEST_BLOCK.finditer(source):
        start = source.find("{", match.end())
        if start == -1:
            continue
        depth = 0
        for index in range(start, len(source)):
            char = source[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    line = source.count("\n", 0, match.start()) + 1
                    blocks.append((source[start + 1 : index], line))
                    break
    return blocks


def check_typescript_source(path: str, source: str) -> list[Issue]:
    issues: list[Issue] = []

    if re.search(r"\.(toMatchSnapshot|toMatchInlineSnapshot)\s*\(", source):
        issues.append(Issue(path, "snapshot assertions are not accepted"))
    if re.search(r"expect\s*\(\s*(?:true|1)\s*\)", source):
        issues.append(Issue(path, "trivial assertion on a literal"))
    if re.search(r"\b(?:it|test|describe)\.skip\s*\(", source):
        issues.append(Issue(path, "skipped test"))
    if re.search(r"setTimeout\s*\(", source) and "useFakeTimers" not in source:
        issues.append(Issue(path, "real timers make the test non-deterministic"))

    blocks = _test_blocks(source)
    if not blocks:
        issues.append(Issue(path, "no it()/test() blocks found"))
    for body, line in blocks:
        if not body.strip():
            issues.append(Issue(path, "empty test body", line))
        elif "expect(" not in body and "assert" not in body:
            issues.append(Issue(path, "test has no assertion", line))
    return issues


def check_source(path: str, source: str) -> list[Issue]:
    if path.endswith(".py"):
        return check_python_source(path, source)
    if path.endswith((".ts", ".tsx")):
        return check_typescript_source(path, source)
    return []
