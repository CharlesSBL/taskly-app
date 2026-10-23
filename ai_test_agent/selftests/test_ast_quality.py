from __future__ import annotations

from verifier.ast_quality import check_python_source, check_source, check_typescript_source


def test_good_python_test_passes() -> None:
    source = (
        "import pytest\n\n"
        "def test_add():\n"
        "    assert add(1, 2) == 3\n\n"
        "def test_rejects():\n"
        "    with pytest.raises(ValueError, match='bad'):\n"
        "        parse('x')\n\n"
        "def test_mock():\n"
        "    repo.list.assert_called_once_with()\n"
    )
    assert check_python_source("backend/tests/test_x.py", source) == []


def test_trivial_assertion_is_flagged() -> None:
    source = "def test_x():\n    assert True\n"
    messages = {issue.message for issue in check_python_source("t.py", source)}
    assert "trivial assertion" in messages
    assert "test_x has no real assertion" in messages


def test_missing_assertion_is_flagged() -> None:
    source = "def test_x():\n    add(1, 2)\n"
    issues = check_python_source("t.py", source)
    assert [issue.message for issue in issues] == ["test_x has no real assertion"]


def test_sleep_and_skip_are_flagged() -> None:
    source = "import time\ndef test_x():\n    time.sleep(1)\n    assert 1 == 1\n"
    messages = [issue.message for issue in check_python_source("t.py", source)]
    assert any("time.sleep" in message for message in messages)
    skipped = "@pytest.mark.skip(reason='later')\ndef test_y():\n    assert 1 == 1\n"
    assert any("skipped" in issue.message for issue in check_python_source("t.py", skipped))


def test_syntax_error_and_empty_module_are_flagged() -> None:
    assert "syntax error" in check_python_source("t.py", "def test_x(:")[0].message
    assert "no test functions" in check_python_source("t.py", "x = 1\n")[0].message


def test_good_typescript_test_passes() -> None:
    source = (
        "it('renders', () => {\n"
        "  render(<Foo />)\n"
        "  expect(screen.getByRole('heading')).toHaveTextContent('Foo')\n"
        "})\n"
    )
    assert check_typescript_source("Foo.test.tsx", source) == []


def test_snapshot_trivial_and_skip_are_flagged() -> None:
    source = (
        "it('snapshot', () => { expect(render(<Foo />)).toMatchSnapshot() })\n"
        "it('trivial', () => { expect(true).toBe(true) })\n"
        "it.skip('later', () => { expect(1).toBe(1) })\n"
    )
    messages = " ".join(issue.message for issue in check_typescript_source("Foo.test.tsx", source))
    assert "snapshot" in messages
    assert "trivial" in messages
    assert "skipped" in messages


def test_empty_and_assertion_free_tests_are_flagged() -> None:
    empty = "it('empty', () => {})\n"
    assert any(
        "empty test body" in issue.message for issue in check_typescript_source("a.test.ts", empty)
    )
    assertion_free = "it('nothing', () => { render(<Foo />) })\n"
    assert any(
        "no assertion" in issue.message
        for issue in check_typescript_source("a.test.ts", assertion_free)
    )
    assert (
        "no it()/test() blocks" in check_typescript_source("a.test.ts", "const x = 1\n")[0].message
    )


def test_real_timers_are_flagged() -> None:
    source = (
        "it('waits', async () => { await new Promise((r) => "
        "setTimeout(r, 10)); expect(1).toBe(1) })\n"
    )
    assert any("timers" in issue.message for issue in check_typescript_source("a.test.ts", source))


def test_check_source_dispatches_by_suffix() -> None:
    assert check_source("a.py", "def test_x():\n    assert 1 == 1\n") == []
    assert check_source("a.md", "anything") == []
