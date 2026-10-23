from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest

from agent.budget import BudgetExceeded, BudgetGuard, CostMeter, Usage, parse_usage, usage_cost
from agent.config import PRICES, Budgets


def test_usage_cost_matches_price_table() -> None:
    price = PRICES["claude-sonnet-5-5"]
    usage = Usage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
    )
    assert usage_cost(usage, price) == Decimal("2") + Decimal("10") + Decimal("2.50") + Decimal(
        "0.10"
    )


def test_meter_accumulates_real_usage_counts() -> None:
    meter = CostMeter(price=PRICES["claude-sonnet-5-5"])
    meter.add(Usage(input_tokens=1000, output_tokens=500))
    meter.add(Usage(input_tokens=1000, output_tokens=500, cache_read_input_tokens=10_000))
    assert meter.usage.input_tokens == 2000
    assert meter.usage.output_tokens == 1000
    assert meter.usage.cache_read_input_tokens == 10_000
    expected = Decimal(2000) * Decimal("2") / Decimal(1_000_000)
    expected += Decimal(1000) * Decimal("10") / Decimal(1_000_000)
    expected += Decimal(10_000) * Decimal("0.10") / Decimal(1_000_000)
    assert meter.total_usd == expected


def test_meter_would_exceed() -> None:
    meter = CostMeter(price=PRICES["claude-sonnet-5-5"])
    meter.add(Usage(input_tokens=400_000))  # $0.80
    assert meter.would_exceed(Decimal("0.75"))
    assert not meter.would_exceed(Decimal("1.00"))


def test_turn_and_file_limits() -> None:
    guard = BudgetGuard(budgets=Budgets(max_turns=2, max_files=1))
    guard.start_turn()
    guard.start_turn()
    with pytest.raises(BudgetExceeded, match="turn limit"):
        guard.start_turn()

    guard.record_file()
    with pytest.raises(BudgetExceeded, match="file limit"):
        guard.record_file()


def test_cost_limit_reports_amounts() -> None:
    guard = BudgetGuard(budgets=Budgets(max_cost_usd=Decimal("0.50")))
    with pytest.raises(BudgetExceeded, match=r"\$0\.60"):
        guard.charge(Decimal("0.60"))
    assert guard.cost_usd == Decimal("0.60")
    assert guard.remaining_usd == Decimal("0")


def test_parse_usage_tolerates_missing_and_invalid_fields() -> None:
    usage = parse_usage(SimpleNamespace(input_tokens=10, output_tokens="nope"))
    assert usage == Usage(input_tokens=10, output_tokens=0)
    assert parse_usage(object()) == Usage()
