from __future__ import annotations

from agent.redaction import REDACTED, redact, redact_text


def test_anthropic_keys_are_redacted() -> None:
    text = "key sk-ant-api03-abcdefghijklmnop end"
    assert "sk-ant" not in redact_text(text)
    assert "[REDACTED_ANTHROPIC_KEY]" in redact_text(text)


def test_github_and_aws_tokens_are_redacted() -> None:
    assert "ghp_" not in redact_text("token ghp_1234567890abcdefghijklmn")
    assert "AKIA" not in redact_text("id AKIAIOSFODNN7EXAMPLE")  # pragma: allowlist secret


def test_bearer_headers_are_redacted() -> None:
    result = redact_text("Authorization: Bearer abcdef1234567890")
    assert result == f"Authorization: Bearer {REDACTED}"


def test_key_value_pairs_are_redacted() -> None:
    result = redact_text("api_key=supersecretvalue token: 'abcdef123'")  # pragma: allowlist secret
    assert "supersecretvalue" not in result
    assert "abcdef123" not in result  # pragma: allowlist secret


def test_nested_structures_are_redacted() -> None:
    payload = {
        # Fake credentials on purpose: this test asserts they are redacted.
        "headers": {"authorization": "Bearer abcdef1234567890"},  # pragma: allowlist secret
        "items": ["sk-ant-api03-abcdefghijklmnop", 3, None],  # pragma: allowlist secret
    }
    result = redact(payload)
    assert result["headers"]["authorization"] == f"Bearer {REDACTED}"
    assert result["items"][0] == "[REDACTED_ANTHROPIC_KEY]"
    assert result["items"][1] == 3


def test_ordinary_text_is_unchanged() -> None:
    text = "The repository uses pytest and Vitest."
    assert redact_text(text) == text
