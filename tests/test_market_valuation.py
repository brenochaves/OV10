from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ov10.domain.enums import InstrumentType
from ov10.domain.models import BookPositionSnapshot, PositionSnapshot
from ov10.reconciliation.market_valuation import build_market_valuation_context


class MarketValuationContextTests(unittest.TestCase):
    def test_build_market_valuation_context_translates_market_value_and_profit(self) -> None:
        positions = [
            PositionSnapshot(
                snapshot_date=date(2026, 3, 20),
                instrument_code="AAPL",
                instrument_type=InstrumentType.STOCK_US,
                quantity=Decimal("10"),
                total_cost=Decimal("100"),
                avg_cost=Decimal("10"),
                currency="USD",
                engine_version="test-engine",
            )
        ]
        book_positions = [
            BookPositionSnapshot(
                snapshot_date=date(2026, 3, 20),
                portfolio_id="portfolio.global",
                book_id="book.global.stocks",
                account_id="account.us",
                instrument_code="AAPL",
                instrument_type=InstrumentType.STOCK_US,
                quantity=Decimal("10"),
                total_cost=Decimal("100"),
                avg_cost=Decimal("10"),
                currency="USD",
                engine_version="test-engine",
            )
        ]
        market_snapshots_by_code = {
            "AAPL": {
                "canonical_code": "AAPL",
                "currency": "USD",
                "price": "12",
                "market": "NASDAQ",
                "absolute_change": "0.5",
                "percent_change": "4.35",
                "provider_metadata": {"longName": "Apple Inc."},
            }
        }
        fx_snapshots_by_pair = {
            ("USD", "BRL"): {
                "base_currency": "USD",
                "quote_currency": "BRL",
                "rate": "5.20",
            }
        }

        context = build_market_valuation_context(
            positions=positions,
            book_positions=book_positions,
            market_snapshots_by_code=market_snapshots_by_code,
            fx_snapshots_by_pair=fx_snapshots_by_pair,
            base_currency="BRL",
        )

        valuation = context.position_valuations["AAPL"]
        self.assertEqual(valuation.price, Decimal("12"))
        self.assertEqual(valuation.price_currency, "USD")
        self.assertEqual(valuation.market_code, "NASDAQ")
        self.assertEqual(valuation.instrument_name, "Apple Inc.")
        self.assertEqual(valuation.avg_cost_in_price_currency, Decimal("10"))
        self.assertEqual(valuation.total_cost_in_base_currency, Decimal("520.0"))
        self.assertEqual(valuation.market_value_in_base_currency, Decimal("624.0"))
        self.assertEqual(valuation.profit_total_in_base_currency, Decimal("104.0"))

        self.assertEqual(context.positions_with_market_value_in_base_currency, 1)
        self.assertEqual(context.valued_book_count, 1)
        self.assertEqual(
            context.book_valuations["book.global.stocks"].current_weight,
            Decimal("1"),
        )
