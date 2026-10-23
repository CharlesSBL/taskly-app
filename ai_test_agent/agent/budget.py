"""Token-based cost accounting and hard run budgets.

Costs are computed from the `usage` block of every API response, never
estimated from prompt length. Cache reads and writes are priced separately
because they dominate the cost of a long tool-use conversation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .config import Budgets, Price

MILLION = Decimal(1_000_000)


class BudgetExceeded(RuntimeError):
    """Raised when a run would exceed one of its hard limits."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


def _token_cost(tokens: int, price: Decimal) -> Decimal:
    return Decimal(tokens) * price / MILLION


def usage_cost(usage: Usage, price: Price) -> Decimal:
    """Return the USD cost of a single response's usage block.

    `input_tokens` excludes cache reads and writes on Anthropic's API, so the
    three categories are additive.
    """
    return (
        _token_cost(usage.input_tokens, price.input)
        + _token_cost(usage.output_tokens, price.output)
        + _token_cost(usage.cache_creation_input_tokens, price.cache_write_5m)
        + _token_cost(usage.cache_read_input_tokens, price.cache_read)
    )


@dataclass
class CostMeter:
    price: Price
    usage: Usage = field(default_factory=Usage)

    def add(self, usage: Usage) -> None:
        self.usage = Usage(
            input_tokens=self.usage.input_tokens + usage.input_tokens,
            output_tokens=self.usage.output_tokens + usage.output_tokens,
            cache_creation_input_tokens=(
                self.usage.cache_creation_input_tokens + usage.cache_creation_input_tokens
            ),
            cache_read_input_tokens=(
                self.usage.cache_read_input_tokens + usage.cache_read_input_tokens
            ),
        )

    @property
    def total_usd(self) -> Decimal:
        return usage_cost(self.usage, self.price)

    def would_exceed(self, limit: Decimal) -> bool:
        return self.total_usd > limit


@dataclass
class BudgetGuard:
    """Enforce turns, files and spend before each expensive operation."""

    budgets: Budgets
    turns: int = 0
    files_written: int = 0
    cost_usd: Decimal = Decimal(0)

    def start_turn(self) -> None:
        if self.turns >= self.budgets.max_turns:
            raise BudgetExceeded(f"turn limit reached ({self.budgets.max_turns})")
        self.turns += 1

    def record_file(self) -> None:
        if self.files_written >= self.budgets.max_files:
            raise BudgetExceeded(f"file limit reached ({self.budgets.max_files})")
        self.files_written += 1

    def charge(self, absolute_cost: Decimal) -> None:
        self.cost_usd = absolute_cost
        if self.cost_usd > self.budgets.max_cost_usd:
            raise BudgetExceeded(
                f"cost limit reached (${self.cost_usd:.4f} > ${self.budgets.max_cost_usd})"
            )

    @property
    def remaining_usd(self) -> Decimal:
        return max(Decimal(0), self.budgets.max_cost_usd - self.cost_usd)


def parse_usage(raw: object) -> Usage:
    """Read a usage block defensively from a real or fake SDK response."""

    def value(name: str) -> int:
        token = getattr(raw, name, 0)
        return int(token) if isinstance(token, int) else 0

    return Usage(
        input_tokens=value("input_tokens"),
        output_tokens=value("output_tokens"),
        cache_creation_input_tokens=value("cache_creation_input_tokens"),
        cache_read_input_tokens=value("cache_read_input_tokens"),
    )
