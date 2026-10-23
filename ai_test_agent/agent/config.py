"""Runtime configuration and verified model pricing.

Model IDs and prices were checked against
https://platform.claude.com/docs/en/about-claude/models/overview and
https://platform.claude.com/docs/en/about-claude/pricing on 2026-10-23.
Prices are US dollars per million tokens. Update this table only after
re-checking those pages; an unknown model ID is a hard error so a typo can
never silently produce a wrong cost.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Literal

Mode = Literal["pr", "backfill"]

PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICING_VERIFIED_ON = "2026-10-23"


@dataclass(frozen=True)
class Price:
    """USD per million tokens."""

    input: Decimal
    output: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal
    cache_read: Decimal


PRICES: dict[str, Price] = {
    "claude-sonnet-5-5": Price(
        input=Decimal("2"),
        output=Decimal("10"),
        cache_write_5m=Decimal("2.50"),
        cache_write_1h=Decimal("4"),
        cache_read=Decimal("0.10"),
    ),
    "claude-haiku-5-5": Price(
        input=Decimal("0.10"),
        output=Decimal("0.50"),
        cache_write_5m=Decimal("0.125"),
        cache_write_1h=Decimal("0.20"),
        cache_read=Decimal("0.01"),
    ),
    "claude-opus-5-5": Price(
        input=Decimal("4"),
        output=Decimal("20"),
        cache_write_5m=Decimal("5"),
        cache_write_1h=Decimal("8"),
        cache_read=Decimal("0.20"),
    ),
}

DEFAULT_MODEL = "claude-sonnet-5-5"


class ConfigError(ValueError):
    """Raised when the environment contains an unusable value."""


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive, got {value}")
    return value


def _env_decimal(name: str, default: Decimal) -> Decimal:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise ConfigError(f"{name} must be a decimal amount, got {raw!r}") from exc
    if value <= 0:
        raise ConfigError(f"{name} must be positive, got {value}")
    return value


@dataclass(frozen=True)
class Budgets:
    max_turns: int = 15
    max_files: int = 15
    max_diff_bytes: int = 40_000
    max_cost_usd: Decimal = Decimal("0.75")
    max_output_tokens: int = 4096

    @classmethod
    def from_env(cls, mode: Mode) -> Budgets:
        default_cost = Decimal("5.00") if mode == "backfill" else Decimal("0.75")
        return cls(
            max_turns=_env_int("TASKLY_MAX_TURNS", 15),
            max_files=_env_int("TASKLY_MAX_FILES", 15),
            max_diff_bytes=_env_int("TASKLY_MAX_DIFF_BYTES", 40_000),
            max_cost_usd=_env_decimal("TASKLY_MAX_COST_USD", default_cost),
            max_output_tokens=_env_int("TASKLY_MAX_OUTPUT_TOKENS", 4096),
        )


@dataclass(frozen=True)
class Settings:
    model: str = DEFAULT_MODEL
    budgets: Budgets = field(default_factory=Budgets)
    pricing_source: str = PRICING_SOURCE
    pricing_verified_on: str = PRICING_VERIFIED_ON

    def __post_init__(self) -> None:
        if self.model not in PRICES:
            known = ", ".join(sorted(PRICES))
            raise ConfigError(f"unknown model {self.model!r}; known models: {known}")

    @property
    def price(self) -> Price:
        return PRICES[self.model]

    @classmethod
    def from_env(cls, mode: Mode = "pr") -> Settings:
        return cls(
            model=os.environ.get("TASKLY_AGENT_MODEL", DEFAULT_MODEL),
            budgets=Budgets.from_env(mode),
        )
