from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _require_upper_code(value: str, field_name: str) -> str:
    return _require_non_empty(value, field_name).upper()


def _require_currency(value: str, field_name: str) -> str:
    normalized = _require_upper_code(value, field_name)
    if len(normalized) != 3:
        raise ValueError(f"{field_name} must have length 3")
    return normalized


def _require_decimal_positive(value: Decimal, field_name: str) -> None:
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be > 0")


def _require_decimal_non_negative(value: Decimal, field_name: str) -> None:
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be >= 0")


def _require_metadata_json(value: str, field_name: str) -> str:
    normalized = _require_non_empty(value, field_name)
    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must contain valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} must encode a JSON object")
    return normalized


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    canonical_code: str
    provider_name: str
    source_symbol: str
    snapshot_date: date
    observed_at: datetime
    retrieved_at: datetime
    currency: str
    price: Decimal
    previous_close: Decimal | None = None
    absolute_change: Decimal | None = None
    percent_change: Decimal | None = None
    market: str | None = None
    quote_status: str = "ok"
    provider_metadata_json: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "canonical_code",
            _require_upper_code(self.canonical_code, "canonical_code"),
        )
        object.__setattr__(
            self,
            "provider_name",
            _require_non_empty(self.provider_name, "provider_name"),
        )
        object.__setattr__(
            self,
            "source_symbol",
            _require_non_empty(self.source_symbol, "source_symbol"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency, "currency"))
        object.__setattr__(
            self,
            "quote_status",
            _require_non_empty(self.quote_status, "quote_status"),
        )
        if self.market is not None:
            object.__setattr__(self, "market", _require_non_empty(self.market, "market"))
        if self.provider_metadata_json is not None:
            object.__setattr__(
                self,
                "provider_metadata_json",
                _require_metadata_json(self.provider_metadata_json, "provider_metadata_json"),
            )
        _require_decimal_positive(self.price, "price")
        if self.previous_close is not None:
            _require_decimal_non_negative(self.previous_close, "previous_close")


@dataclass(frozen=True, slots=True)
class FxSnapshot:
    provider_name: str
    base_currency: str
    quote_currency: str
    snapshot_date: date
    observed_at: datetime
    retrieved_at: datetime
    rate: Decimal
    rate_kind: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    bulletin_type: str | None = None
    provider_metadata_json: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "provider_name",
            _require_non_empty(self.provider_name, "provider_name"),
        )
        object.__setattr__(
            self,
            "base_currency",
            _require_currency(self.base_currency, "base_currency"),
        )
        object.__setattr__(
            self,
            "quote_currency",
            _require_currency(self.quote_currency, "quote_currency"),
        )
        object.__setattr__(self, "rate_kind", _require_non_empty(self.rate_kind, "rate_kind"))
        if self.bulletin_type is not None:
            object.__setattr__(
                self,
                "bulletin_type",
                _require_non_empty(self.bulletin_type, "bulletin_type"),
            )
        if self.provider_metadata_json is not None:
            object.__setattr__(
                self,
                "provider_metadata_json",
                _require_metadata_json(self.provider_metadata_json, "provider_metadata_json"),
            )
        _require_decimal_positive(self.rate, "rate")
        if self.bid is not None:
            _require_decimal_positive(self.bid, "bid")
        if self.ask is not None:
            _require_decimal_positive(self.ask, "ask")


@dataclass(frozen=True, slots=True)
class MarketProviderResult:
    snapshots: tuple[MarketSnapshot, ...]
    unresolved_codes: tuple[str, ...] = ()
    request_failed_codes: tuple[str, ...] = ()
