from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ov10.domain.models import BookPositionSnapshot, PositionSnapshot


def _to_decimal(value: object) -> Decimal | None:
    if value in {None, ""}:
        return None
    return Decimal(str(value))


def _to_string(value: object) -> str | None:
    if isinstance(value, str):
        normalized = value.strip()
        return normalized or None
    return None


@dataclass(frozen=True, slots=True)
class PositionValuation:
    instrument_code: str
    price: Decimal | None
    price_currency: str | None
    market_code: str | None
    instrument_name: str | None
    absolute_change: Decimal | None
    percent_change: Decimal | None
    avg_cost_in_price_currency: Decimal | None
    total_cost_in_base_currency: Decimal | None
    market_value_in_base_currency: Decimal | None
    profit_total_in_base_currency: Decimal | None
    market_fx_rate_to_base_currency: Decimal | None
    cost_fx_rate_to_price_currency: Decimal | None


@dataclass(frozen=True, slots=True)
class BookValuation:
    book_id: str
    market_value_in_base_currency: Decimal | None
    total_cost_in_base_currency: Decimal | None
    profit_total_in_base_currency: Decimal | None
    current_weight: Decimal | None


@dataclass(frozen=True, slots=True)
class MarketValuationContext:
    base_currency: str
    position_valuations: dict[str, PositionValuation]
    book_valuations: dict[str, BookValuation]
    position_count: int
    book_count: int
    positions_with_market_price: int
    positions_with_market_code: int
    positions_with_display_name: int
    positions_with_change: int
    positions_with_change_pct: int
    positions_with_price_currency: int
    positions_with_avg_cost_in_price_currency: int
    positions_with_market_value_in_base_currency: int
    positions_with_profit_total_in_base_currency: int
    valued_book_count: int
    books_with_profit_total: int
    books_with_current_weight: int
    total_market_value_in_base_currency: Decimal
    total_cost_in_base_currency: Decimal


def build_market_valuation_context(
    *,
    positions: list[PositionSnapshot] | tuple[PositionSnapshot, ...],
    book_positions: list[BookPositionSnapshot] | tuple[BookPositionSnapshot, ...],
    market_snapshots_by_code: dict[str, dict[str, object]],
    fx_snapshots_by_pair: dict[tuple[str, str], dict[str, object]],
    base_currency: str = "BRL",
) -> MarketValuationContext:
    normalized_base_currency = base_currency.strip().upper()
    position_valuations: dict[str, PositionValuation] = {}
    total_market_value = Decimal("0")
    total_cost_value = Decimal("0")

    for item in positions:
        valuation = _build_position_valuation(
            position=item,
            market_snapshot=market_snapshots_by_code.get(item.instrument_code),
            fx_snapshots_by_pair=fx_snapshots_by_pair,
            base_currency=normalized_base_currency,
        )
        position_valuations[item.instrument_code] = valuation
        if valuation.market_value_in_base_currency is not None:
            total_market_value += valuation.market_value_in_base_currency
        if valuation.total_cost_in_base_currency is not None:
            total_cost_value += valuation.total_cost_in_base_currency

    book_totals: dict[str, dict[str, Decimal | int]] = {}
    for item in book_positions:
        bucket = book_totals.setdefault(
            item.book_id,
            {
                "market_value": Decimal("0"),
                "total_cost": Decimal("0"),
                "profit_total": Decimal("0"),
                "market_count": 0,
                "profit_count": 0,
                "position_count": 0,
            },
        )
        bucket["position_count"] = int(bucket["position_count"]) + 1
        valuation = position_valuations.get(item.instrument_code)
        if valuation is None:
            continue
        if valuation.market_value_in_base_currency is not None:
            bucket["market_value"] = (
                Decimal(bucket["market_value"]) + valuation.market_value_in_base_currency
            )
            bucket["total_cost"] = Decimal(bucket["total_cost"]) + (
                valuation.total_cost_in_base_currency or Decimal("0")
            )
            bucket["market_count"] = int(bucket["market_count"]) + 1
        if valuation.profit_total_in_base_currency is not None:
            bucket["profit_total"] = (
                Decimal(bucket["profit_total"]) + valuation.profit_total_in_base_currency
            )
            bucket["profit_count"] = int(bucket["profit_count"]) + 1

    book_valuations: dict[str, BookValuation] = {}
    for book_id, bucket in sorted(book_totals.items()):
        position_count = int(bucket["position_count"])
        market_count = int(bucket["market_count"])
        profit_count = int(bucket["profit_count"])
        market_value = None
        total_cost = None
        profit_total = None
        if market_count == position_count and position_count > 0:
            market_value = Decimal(bucket["market_value"])
            total_cost = Decimal(bucket["total_cost"])
        if profit_count == position_count and position_count > 0:
            profit_total = Decimal(bucket["profit_total"])

        current_weight = None
        if market_value is not None and total_market_value > 0:
            current_weight = market_value / total_market_value
        book_valuations[book_id] = BookValuation(
            book_id=book_id,
            market_value_in_base_currency=market_value,
            total_cost_in_base_currency=total_cost,
            profit_total_in_base_currency=profit_total,
            current_weight=current_weight,
        )

    position_values = list(position_valuations.values())
    book_values = list(book_valuations.values())
    return MarketValuationContext(
        base_currency=normalized_base_currency,
        position_valuations=position_valuations,
        book_valuations=book_valuations,
        position_count=len(position_values),
        book_count=len(book_values),
        positions_with_market_price=sum(item.price is not None for item in position_values),
        positions_with_market_code=sum(item.market_code is not None for item in position_values),
        positions_with_display_name=sum(
            item.instrument_name is not None for item in position_values
        ),
        positions_with_change=sum(item.absolute_change is not None for item in position_values),
        positions_with_change_pct=sum(item.percent_change is not None for item in position_values),
        positions_with_price_currency=sum(
            item.price_currency is not None for item in position_values
        ),
        positions_with_avg_cost_in_price_currency=sum(
            item.avg_cost_in_price_currency is not None for item in position_values
        ),
        positions_with_market_value_in_base_currency=sum(
            item.market_value_in_base_currency is not None for item in position_values
        ),
        positions_with_profit_total_in_base_currency=sum(
            item.profit_total_in_base_currency is not None for item in position_values
        ),
        valued_book_count=sum(
            item.market_value_in_base_currency is not None for item in book_values
        ),
        books_with_profit_total=sum(
            item.profit_total_in_base_currency is not None for item in book_values
        ),
        books_with_current_weight=sum(item.current_weight is not None for item in book_values),
        total_market_value_in_base_currency=total_market_value,
        total_cost_in_base_currency=total_cost_value,
    )


def _build_position_valuation(
    *,
    position: PositionSnapshot,
    market_snapshot: dict[str, object] | None,
    fx_snapshots_by_pair: dict[tuple[str, str], dict[str, object]],
    base_currency: str,
) -> PositionValuation:
    if market_snapshot is None:
        return PositionValuation(
            instrument_code=position.instrument_code,
            price=None,
            price_currency=None,
            market_code=None,
            instrument_name=None,
            absolute_change=None,
            percent_change=None,
            avg_cost_in_price_currency=None,
            total_cost_in_base_currency=None,
            market_value_in_base_currency=None,
            profit_total_in_base_currency=None,
            market_fx_rate_to_base_currency=None,
            cost_fx_rate_to_price_currency=None,
        )

    price = _to_decimal(market_snapshot.get("price"))
    price_currency = _to_string(market_snapshot.get("currency"))
    market_code = _to_string(market_snapshot.get("market"))
    absolute_change = _to_decimal(market_snapshot.get("absolute_change"))
    percent_change = _to_decimal(market_snapshot.get("percent_change"))
    metadata = market_snapshot.get("provider_metadata")
    instrument_name = None
    if isinstance(metadata, dict):
        instrument_name = _to_string(metadata.get("longName"))

    market_fx_rate = _resolve_fx_rate(
        from_currency=price_currency,
        to_currency=base_currency,
        fx_snapshots_by_pair=fx_snapshots_by_pair,
    )
    cost_to_base_currency = _resolve_fx_rate(
        from_currency=position.currency,
        to_currency=base_currency,
        fx_snapshots_by_pair=fx_snapshots_by_pair,
    )
    cost_to_price_currency = _resolve_fx_rate(
        from_currency=position.currency,
        to_currency=price_currency,
        fx_snapshots_by_pair=fx_snapshots_by_pair,
    )

    avg_cost_in_price_currency = None
    if cost_to_price_currency is not None:
        avg_cost_in_price_currency = position.avg_cost * cost_to_price_currency

    total_cost_in_base_currency = None
    if cost_to_base_currency is not None:
        total_cost_in_base_currency = position.total_cost * cost_to_base_currency

    market_value_in_base_currency = None
    if price is not None and market_fx_rate is not None:
        market_value_in_base_currency = position.quantity * price * market_fx_rate

    profit_total_in_base_currency = None
    if market_value_in_base_currency is not None and total_cost_in_base_currency is not None:
        profit_total_in_base_currency = market_value_in_base_currency - total_cost_in_base_currency

    return PositionValuation(
        instrument_code=position.instrument_code,
        price=price,
        price_currency=price_currency,
        market_code=market_code,
        instrument_name=instrument_name,
        absolute_change=absolute_change,
        percent_change=percent_change,
        avg_cost_in_price_currency=avg_cost_in_price_currency,
        total_cost_in_base_currency=total_cost_in_base_currency,
        market_value_in_base_currency=market_value_in_base_currency,
        profit_total_in_base_currency=profit_total_in_base_currency,
        market_fx_rate_to_base_currency=market_fx_rate,
        cost_fx_rate_to_price_currency=cost_to_price_currency,
    )


def _resolve_fx_rate(
    *,
    from_currency: str | None,
    to_currency: str | None,
    fx_snapshots_by_pair: dict[tuple[str, str], dict[str, object]],
) -> Decimal | None:
    if from_currency is None or to_currency is None:
        return None
    normalized_from = from_currency.strip().upper()
    normalized_to = to_currency.strip().upper()
    if normalized_from == normalized_to:
        return Decimal("1")

    direct = fx_snapshots_by_pair.get((normalized_from, normalized_to))
    if direct is not None:
        direct_rate = _to_decimal(direct.get("rate"))
        if direct_rate is not None:
            return direct_rate

    inverse = fx_snapshots_by_pair.get((normalized_to, normalized_from))
    if inverse is not None:
        inverse_rate = _to_decimal(inverse.get("rate"))
        if inverse_rate is not None and inverse_rate != Decimal("0"):
            return Decimal("1") / inverse_rate

    return None
