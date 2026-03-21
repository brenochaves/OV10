from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from ov10.cli import main
from ov10.domain import (
    CanonicalDividendReceipt,
    CanonicalTransaction,
    DividendType,
    ImportBatch,
    IngestionBundle,
    InstrumentType,
    SourceRecord,
    SourceSystem,
    TransactionType,
)
from ov10.reference import build_instrument_references
from ov10.services import persist_status_invest_xlsx

FIXTURE_PATH = Path("data/OV10_base_2025.xlsx")


class InstrumentReferenceTests(unittest.TestCase):
    def test_build_instrument_references_from_fixture(self) -> None:
        from ov10.ingestion import load_status_invest_workbook

        bundle = load_status_invest_workbook(FIXTURE_PATH)
        references = build_instrument_references(bundle)

        self.assertEqual(len(references), 160)
        self.assertTrue(
            all(item.canonical_code == item.canonical_code.upper() for item in references)
        )
        self.assertTrue(any(item.instrument_type != InstrumentType.UNKNOWN for item in references))
        self.assertTrue(all(item.instrument_type != InstrumentType.UNKNOWN for item in references))
        self.assertTrue(
            all(
                item.identity_status
                in {"observed_identity", "observed_only", "observed_with_conflict"}
                for item in references
            )
        )
        self.assertTrue(all(item.identity_status == "observed_identity" for item in references))

    def test_conflicting_identity_is_marked_explicitly(self) -> None:
        batch = ImportBatch(
            batch_id="batch:conflict",
            source_system=SourceSystem.STATUS_INVEST_XLSX,
            source_file="synthetic.xlsx",
            file_sha256="hash",
            imported_at=datetime(2026, 3, 19, 12, 0, tzinfo=UTC),
        )
        source_record_1 = SourceRecord(
            batch_id=batch.batch_id,
            source_system=batch.source_system,
            source_file=batch.source_file,
            sheet_name="Operações",
            row_number=2,
            source_row_ref="Operações!2",
        )
        source_record_2 = SourceRecord(
            batch_id=batch.batch_id,
            source_system=batch.source_system,
            source_file=batch.source_file,
            sheet_name="Proventos",
            row_number=2,
            source_row_ref="Proventos!2",
        )
        bundle = IngestionBundle(
            batch=batch,
            transactions=(
                CanonicalTransaction(
                    transaction_id="tx-1",
                    source_record=source_record_1,
                    trade_date=date(2026, 1, 10),
                    transaction_type=TransactionType.BUY,
                    instrument_code="ABCD4",
                    instrument_type=InstrumentType.STOCK_BR,
                    asset_category="Ações",
                    broker_name="XP",
                    quantity=Decimal("10"),
                    unit_price=Decimal("10"),
                    gross_amount=Decimal("100"),
                    fees=Decimal("0"),
                    cash_effect=Decimal("-100"),
                ),
            ),
            dividend_receipts=(
                CanonicalDividendReceipt(
                    receipt_id="div-1",
                    source_record=source_record_2,
                    reference_date=date(2026, 1, 5),
                    received_date=date(2026, 1, 15),
                    instrument_code="ABCD4",
                    instrument_type=InstrumentType.BDR,
                    asset_category="BDR",
                    broker_name="XP",
                    dividend_type=DividendType.DIVIDEND,
                    payable_quantity=Decimal("10"),
                    gross_amount=Decimal("1"),
                    withholding_tax=Decimal("0"),
                    net_amount=Decimal("1"),
                ),
            ),
            corporate_actions=(),
        )

        references = build_instrument_references(bundle)

        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].canonical_code, "ABCD4")
        self.assertEqual(references[0].instrument_type, InstrumentType.BDR)
        self.assertEqual(references[0].identity_status, "observed_with_conflict")
        self.assertIn("Observed instrument types", references[0].notes or "")

    def test_cli_instrument_reference_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"
            report = persist_status_invest_xlsx(FIXTURE_PATH, database_path=database_path)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "instrument-reference-report",
                        "--database",
                        str(database_path),
                        "--batch-id",
                        report.batch_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["counts"]["instrument_references"], 160)
            self.assertEqual(payload["counts"]["instrument_aliases"], 160)
            self.assertIn("observed_identity", payload["counts"]["identity_statuses"])
            self.assertTrue(payload["references"])
            self.assertIn("alias_count", payload["references"][0])
            self.assertIn("observation_counts", payload["references"][0])
