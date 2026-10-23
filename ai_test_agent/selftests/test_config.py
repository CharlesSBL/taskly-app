from __future__ import annotations

from decimal import Decimal

import pytest

from agent.config import Budgets, ConfigError, Price, Settings


def test_the_live_tested_provider_is_the_default() -> None:
    settings = Settings()
    assert settings.provider == "deepseek"
    assert settings.model == "deepseek-flash"
    assert settings.price.input == Decimal("0.30")
    assert settings.price.output == Decimal("1.20")
    assert settings.api_key_env == "DEEPSEEK_API_KEY"  # pragma: allowlist secret


def test_anthropic_is_still_available_as_an_opt_in() -> None:
    settings = Settings(provider="anthropic")
    assert settings.model == "claude-sonnet-5-5"
    assert settings.price.input == Decimal("2")
    assert settings.price.output == Decimal("10")
    assert settings.base_url is None


def test_unknown_model_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_AGENT_MODEL", "claude-2.0")
    with pytest.raises(ConfigError, match="unknown model"):
        Settings.from_env()


def test_env_overrides_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_MAX_TURNS", "3")
    monkeypatch.setenv("TASKLY_MAX_COST_USD", "1.25")
    settings = Settings.from_env("pr")
    assert settings.budgets.max_turns == 3
    assert settings.budgets.max_cost_usd == Decimal("1.25")


def test_backfill_has_a_higher_default_ceiling() -> None:
    assert Budgets.from_env("pr").max_cost_usd == Decimal("0.75")
    assert Budgets.from_env("backfill").max_cost_usd == Decimal("5.00")


def test_invalid_budget_values_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_MAX_TURNS", "many")
    with pytest.raises(ConfigError, match="integer"):
        Budgets.from_env("pr")
    monkeypatch.setenv("TASKLY_MAX_TURNS", "0")
    with pytest.raises(ConfigError, match="positive"):
        Budgets.from_env("pr")


def test_price_is_immutable() -> None:
    price = Price(
        input=Decimal(1),
        output=Decimal(2),
        cache_write_5m=Decimal(3),
        cache_write_1h=Decimal(4),
        cache_read=Decimal(5),
    )
    with pytest.raises(AttributeError):
        price.input = Decimal(9)  # type: ignore[misc]


def test_deepseek_provider_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "deepseek")
    monkeypatch.delenv("TASKLY_AGENT_MODEL", raising=False)
    settings = Settings.from_env()
    assert settings.model == "deepseek-flash"
    assert settings.base_url == "https://api.deepseek.com/anthropic"
    assert settings.api_key_env == "DEEPSEEK_API_KEY"  # pragma: allowlist secret
    assert settings.price.input == Decimal("0.30")
    assert settings.price.output == Decimal("1.20")


def test_deepseek_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "deepseek")
    monkeypatch.setenv("TASKLY_AGENT_MODEL", "deepseek-v4-pro")
    settings = Settings.from_env("backfill")
    assert settings.model == "deepseek-v4-pro"
    assert settings.price.input == Decimal("1.32")
    assert settings.budgets.max_cost_usd == Decimal("5.00")


def test_provider_is_case_insensitive_and_empty_model_is_ignored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", " DeepSeek ")
    monkeypatch.setenv("TASKLY_AGENT_MODEL", "  ")
    assert Settings.from_env().model == "deepseek-flash"


def test_unknown_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "openai")
    with pytest.raises(ConfigError, match="unknown provider"):
        Settings.from_env()


def test_model_must_belong_to_the_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TASKLY_AGENT_PROVIDER", "deepseek")
    monkeypatch.setenv("TASKLY_AGENT_MODEL", "claude-sonnet-5-5")
    with pytest.raises(ConfigError, match="for provider 'deepseek'"):
        Settings.from_env()
