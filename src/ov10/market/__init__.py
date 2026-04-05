"""Governed public market and FX snapshot utilities."""

from typing import TYPE_CHECKING, Any

from ov10.market.models import FxSnapshot, MarketProviderResult, MarketSnapshot
from ov10.market.providers import BCBPTAXProvider, BrapiQuoteProvider

if TYPE_CHECKING:
    from ov10.market.services import (
        DEFAULT_FX_BASE_CURRENCIES,
        PublicMarketRefreshReport,
        SkippedSnapshotRequest,
        refresh_public_market_data,
    )

__all__ = [
    "BCBPTAXProvider",
    "BrapiQuoteProvider",
    "DEFAULT_FX_BASE_CURRENCIES",
    "FxSnapshot",
    "MarketProviderResult",
    "MarketSnapshot",
    "PublicMarketRefreshReport",
    "SkippedSnapshotRequest",
    "refresh_public_market_data",
]


def __getattr__(name: str) -> Any:
    if name in {
        "DEFAULT_FX_BASE_CURRENCIES",
        "PublicMarketRefreshReport",
        "SkippedSnapshotRequest",
        "refresh_public_market_data",
    }:
        from ov10.market import services as _services

        return getattr(_services, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
