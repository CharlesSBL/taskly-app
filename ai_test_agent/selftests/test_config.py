from __future__ import annotations

from decimal import Decimal

import pytest

from agent.config import Budgets, ConfigError, Price, Settings


def test_default_model_is_priced() -> None:
    settings = Settings()
    assert settings.model == "claude-sonnet-5-5"
    assert settings.price.input == Decimal("2")
    assert settings.price.output == Decimal("10")


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
