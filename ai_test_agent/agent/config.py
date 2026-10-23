"""Runtime configuration and verified model pricing.

Models and prices were checked on 2026-10-23:

- Anthropic: https://platform.claude.com/docs/en/about-claude/models/overview
  and https://platform.claude.com/docs/en/about-claude/pricing
- DeepSeek: https://api-docs.deepseek.com/quick_start/pricing
  and https://api-docs.deepseek.com/guides/anthropic_api

Prices are US dollars per million tokens. DeepSeek has peak and off-peak
rates; this table uses the peak (higher) rates so budgets are conservative.
DeepSeek does not charge separately for cache writes, so those tokens are
priced like cache misses.

The provider selects the API key variable and, for DeepSeek, the
Anthropic-compatible base URL. Both providers use the official `anthropic`
SDK: DeepSeek documents the same Messages API, tools and tool_result format.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Literal, cast

Provider = Literal["anthropic", "deepseek"]
Mode = Literal["pr", "backfill"]

ANTHROPIC_PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
DEEPSEEK_PRICING_SOURCE = "https://api-docs.deepseek.com/quick_start/pricing"
ANTHROPIC_PRICING_VERIFIED_ON = "2026-10-23"
DEEPSEEK_PRICING_VERIFIED_ON = "2026-10-23"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"


@dataclass(frozen=True)
class Price:
    """USD per million tokens."""

    input: Decimal
    output: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal
    cache_read: Decimal


ANTHROPIC_PRICES: dict[str, Price] = {
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

DEEPSEEK_PRICES: dict[str, Price] = {
    # DeepSeek-V4.1-Flash, peak rates.
    "deepseek-flash": Price(
        input=Decimal("0.30"),
        output=Decimal("1.20"),
        cache_write_5m=Decimal("0.30"),
        cache_write_1h=Decimal("0.30"),
        cache_read=Decimal("0.006"),
    ),
    # DeepSeek-V4-Pro, peak rates.
    "deepseek-v4-pro": Price(
        input=Decimal("1.32"),
        output=Decimal("3.96"),
        cache_write_5m=Decimal("1.32"),
        cache_write_1h=Decimal("1.32"),
        cache_read=Decimal("0.044"),
    ),
}

# Backwards-compatible alias for the Anthropic table.
PRICES = ANTHROPIC_PRICES

# The default is the provider whose path is exercised by the live runs
# documented in SOLUTION.md. Anthropic is still fully supported through
# TASKLY_AGENT_PROVIDER=anthropic; it is opt-in because no live run has been
# recorded for it yet.
DEFAULT_PROVIDER: Provider = "deepseek"
DEFAULT_MODEL = "claude-sonnet-5-5"


@dataclass(frozen=True)
class ProviderConfig:
    default_model: str
    base_url: str | None
    api_key_env: str
    pricing_source: str
    pricing_verified_on: str
    prices: dict[str, Price]


PROVIDERS: dict[str, ProviderConfig] = {
    "anthropic": ProviderConfig(
        default_model=DEFAULT_MODEL,
        base_url=None,
        api_key_env="ANTHROPIC_API_KEY",  # pragma: allowlist secret
        pricing_source=ANTHROPIC_PRICING_SOURCE,
        pricing_verified_on=ANTHROPIC_PRICING_VERIFIED_ON,
        prices=ANTHROPIC_PRICES,
    ),
    "deepseek": ProviderConfig(
        default_model="deepseek-flash",
        base_url=DEEPSEEK_BASE_URL,
        api_key_env="DEEPSEEK_API_KEY",  # pragma: allowlist secret
        pricing_source=DEEPSEEK_PRICING_SOURCE,
        pricing_verified_on=DEEPSEEK_PRICING_VERIFIED_ON,
        prices=DEEPSEEK_PRICES,
    ),
}


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
    max_output_tokens: int = 8192

    @classmethod
    def from_env(cls, mode: Mode) -> Budgets:
        default_cost = Decimal("5.00") if mode == "backfill" else Decimal("0.75")
        return cls(
            max_turns=_env_int("TASKLY_MAX_TURNS", 15),
            max_files=_env_int("TASKLY_MAX_FILES", 15),
            max_diff_bytes=_env_int("TASKLY_MAX_DIFF_BYTES", 40_000),
            max_cost_usd=_env_decimal("TASKLY_MAX_COST_USD", default_cost),
            max_output_tokens=_env_int("TASKLY_MAX_OUTPUT_TOKENS", 8192),
        )


@dataclass(frozen=True)
class Settings:
    provider: Provider = DEFAULT_PROVIDER
    model: str = ""
    budgets: Budgets = field(default_factory=Budgets)

    def __post_init__(self) -> None:
        config = PROVIDERS.get(self.provider)
        if config is None:
            known = ", ".join(sorted(PROVIDERS))
            raise ConfigError(f"unknown provider {self.provider!r}; known providers: {known}")
        model = self.model or config.default_model
        object.__setattr__(self, "model", model)
        if model not in config.prices:
            known = ", ".join(sorted(config.prices))
            raise ConfigError(
                f"unknown model {model!r} for provider {self.provider!r}; known: {known}"
            )

    @property
    def provider_config(self) -> ProviderConfig:
        return PROVIDERS[self.provider]

    @property
    def price(self) -> Price:
        return self.provider_config.prices[self.model]

    @property
    def base_url(self) -> str | None:
        return self.provider_config.base_url

    @property
    def api_key_env(self) -> str:
        return self.provider_config.api_key_env

    @property
    def pricing_source(self) -> str:
        return self.provider_config.pricing_source

    @property
    def pricing_verified_on(self) -> str:
        return self.provider_config.pricing_verified_on

    @classmethod
    def from_env(cls, mode: Mode = "pr") -> Settings:
        provider = os.environ.get("TASKLY_AGENT_PROVIDER", DEFAULT_PROVIDER).strip().lower()
        provider = provider or DEFAULT_PROVIDER
        if provider not in PROVIDERS:
            known = ", ".join(sorted(PROVIDERS))
            raise ConfigError(f"unknown provider {provider!r}; known providers: {known}")
        model = os.environ.get("TASKLY_AGENT_MODEL", "").strip()
        return cls(
            provider=cast(Provider, provider),
            model=model,
            budgets=Budgets.from_env(mode),
        )
