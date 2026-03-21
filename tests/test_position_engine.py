from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from ov10.domain.enums import InstrumentType, SourceSystem, TransactionType
from ov10.domain.models import CanonicalTransaction, SourceRecord
from ov10.positions import POSITION_ENGINE_VERSION, compute_positions


def _make_transaction(
    *,
    transaction_id: str,
    trade_date: date,
    transaction_type: TransactionType,
    instrument_code: str,
    quantity: str,
    unit_price: str,
    gross_amount: str,
    cash_effect: str,
    cost_basis_effect: str | None,
) -> CanonicalTransaction:
    return CanonicalTransaction(
        transaction_id=transaction_id,
        source_record=SourceRecord(
            batch_id="batch-1",
            source_system=SourceSystem.STATUS_INVEST_XLSX,
            source_file="fixture.xlsx",
            sheet_name="Operações",
            row_number=2,
            source_row_ref="Operações!2",
        ),
        trade_date=trade_date,
        transaction_type=transaction_type,
        instrument_code=instrument_code,
        instrument_type=InstrumentType.STOCK_BR,
        asset_category="Ações",
        broker_name="Broker",
        quantity=Decimal(quantity),
        unit_price=Decimal(unit_price),
        gross_amount=Decimal(gross_amount),
        fees=Decimal("0"),
        cash_effect=Decimal(cash_effect),
        cost_basis_effect=None if cost_basis_effect is None else Decimal(cost_basis_effect),
        currency="BRL",
    )


class AverageCostEngineTests(unittest.TestCase):
    def test_average_cost_engine_handles_partial_sale(self) -> None:
        transactions = [
            _make_transaction(
                transaction_id="t1",
                trade_date=date(2024, 1, 10),
                transaction_type=TransactionType.BUY,
                instrument_code="ABCD3",
                quantity="10",
                unit_price="10",
                gross_amount="100",
                cash_effect="-100",
                cost_basis_effect="100",
            ),
            _make_transaction(
                transaction_id="t2",
                trade_date=date(2024, 2, 10),
                transaction_type=TransactionType.BUY,
                instrument_code="ABCD3",
                quantity="5",
                unit_price="20",
                gross_amount="100",
                cash_effect="-100",
                cost_basis_effect="100",
            ),
            _make_transaction(
                transaction_id="t3",
                trade_date=date(2024, 3, 10),
                transaction_type=TransactionType.SELL,
                instrument_code="ABCD3",
                quantity="6",
                unit_price="20",
                gross_amount="120",
                cash_effect="120",
                cost_basis_effect=None,
            ),
        ]

        snapshots = compute_positions(transactions, snapshot_date=date(2024, 3, 10))

        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        self.assertEqual(snapshot.engine_version, POSITION_ENGINE_VERSION)
        self.assertEqual(snapshot.quantity, Decimal("9"))
        self.assertEqual(snapshot.total_cost, Decimal("120"))
        self.assertEqual(snapshot.avg_cost, Decimal("13.33333333333333333333333333"))

    def test_average_cost_engine_handles_bonus_without_new_cost(self) -> None:
        transactions = [
            _make_transaction(
                transaction_id="t1",
                trade_date=date(2024, 1, 10),
                transaction_type=TransactionType.BUY,
                instrument_code="BNSF3",
                quantity="10",
                unit_price="10",
                gross_amount="100",
                cash_effect="-100",
                cost_basis_effect="100",
            ),
            _make_transaction(
                transaction_id="t2",
                trade_date=date(2024, 2, 10),
                transaction_type=TransactionType.BONUS,
                instrument_code="BNSF3",
                quantity="2",
                unit_price="0",
                gross_amount="0",
                cash_effect="0",
                cost_basis_effect="0",
            ),
        ]

        snapshots = compute_positions(transactions, snapshot_date=date(2024, 2, 10))

        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        self.assertEqual(snapshot.quantity, Decimal("12"))
        self.assertEqual(snapshot.total_cost, Decimal("100"))
        self.assertEqual(snapshot.avg_cost, Decimal("8.333333333333333333333333333"))

    def test_average_cost_engine_handles_conversion_pair(self) -> None:
        transactions = [
            _make_transaction(
                transaction_id="t1",
                trade_date=date(2024, 1, 10),
                transaction_type=TransactionType.BUY,
                instrument_code="OLD3",
                quantity="10",
                unit_price="10",
                gross_amount="100",
                cash_effect="-100",
                cost_basis_effect="100",
            ),
            _make_transaction(
                transaction_id="t2",
                trade_date=date(2024, 2, 10),
                transaction_type=TransactionType.CONVERSION_OUT,
                instrument_code="OLD3",
                quantity="10",
                unit_price="10",
                gross_amount="100",
                cash_effect="0",
                cost_basis_effect="-100",
            ),
            _make_transaction(
                transaction_id="t3",
                trade_date=date(2024, 2, 10),
                transaction_type=TransactionType.CONVERSION_IN,
                instrument_code="NEW3",
                quantity="11",
                unit_price="9.0909090909",
                gross_amount="100",
                cash_effect="0",
                cost_basis_effect="100",
            ),
        ]

        snapshots = compute_positions(transactions, snapshot_date=date(2024, 2, 10))

        self.assertEqual(len(snapshots), 1)
        snapshot = snapshots[0]
        self.assertEqual(snapshot.instrument_code, "NEW3")
        self.assertEqual(snapshot.quantity, Decimal("11"))
        self.assertEqual(snapshot.total_cost, Decimal("100"))
