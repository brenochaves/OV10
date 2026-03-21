from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ov10.cli import main
from ov10.services import persist_status_invest_xlsx
from ov10.storage import SQLiteOV10Store

FIXTURE_PATH = Path("data/OV10_base_2025.xlsx")
REFERENCE_WORKBOOK_PATH = next(Path("ov10_codex_handoff").glob("*.xlsx"))


class PersistenceTests(unittest.TestCase):
    def test_persist_status_invest_xlsx_is_idempotent_for_canonical_facts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"

            first_report = persist_status_invest_xlsx(FIXTURE_PATH, database_path=database_path)
            second_report = persist_status_invest_xlsx(FIXTURE_PATH, database_path=database_path)

            self.assertTrue(first_report.batch_created)
            self.assertFalse(second_report.batch_created)
            self.assertTrue(first_report.config_path.endswith("config\\ov10_portfolio.toml"))
            self.assertEqual(first_report.portfolios_loaded, 1)
            self.assertEqual(first_report.books_loaded, 5)
            self.assertEqual(first_report.accounts_observed, 7)
            self.assertEqual(first_report.account_assignments_persisted, 7)
            self.assertEqual(first_report.transactions_inserted, 1025)
            self.assertEqual(second_report.transactions_inserted, 0)
            self.assertEqual(first_report.dividend_receipts_inserted, 1486)
            self.assertEqual(second_report.dividend_receipts_inserted, 0)
            self.assertEqual(first_report.corporate_actions_inserted, 5)
            self.assertEqual(second_report.corporate_actions_inserted, 0)
            self.assertEqual(first_report.mappings_observed, 160)
            self.assertEqual(first_report.instrument_references_persisted, 160)
            self.assertEqual(first_report.cash_movements_persisted, 2493)
            self.assertEqual(first_report.cash_balance_snapshots_persisted, 7)
            self.assertEqual(first_report.account_position_snapshots_persisted, 21)
            self.assertEqual(first_report.book_position_snapshots_persisted, 21)
            self.assertEqual(first_report.snapshots_persisted, 21)
            self.assertEqual(second_report.snapshots_persisted, 21)
            self.assertEqual(first_report.reconciliation.issue_count, 2)
            self.assertEqual(second_report.reconciliation.issue_count, 2)
            self.assertFalse(first_report.reconciliation.has_errors)
            self.assertEqual(
                {item.code for item in first_report.reconciliation.issues},
                {"conversion_alignment_mismatch"},
            )

            with SQLiteOV10Store(database_path) as store:
                store.initialize()
                self.assertEqual(store.count_rows("import_batch"), 1)
                self.assertEqual(store.count_rows("portfolio_registry"), 1)
                self.assertEqual(store.count_rows("book_registry"), 5)
                self.assertEqual(store.count_rows("account_registry"), 7)
                self.assertEqual(store.count_rows("account_portfolio_assignment"), 7)
                self.assertEqual(store.count_rows("source_record"), 2516)
                self.assertEqual(store.count_rows("canonical_transaction"), 1025)
                self.assertEqual(store.count_rows("canonical_dividend_receipt"), 1486)
                self.assertEqual(store.count_rows("canonical_corporate_action"), 5)
                self.assertEqual(store.count_rows("cash_movement"), 2493)
                self.assertEqual(store.count_rows("cash_balance_snapshot"), 7)
                self.assertEqual(store.count_rows("account_position_snapshot"), 21)
                self.assertEqual(store.count_rows("book_position_snapshot"), 21)
                self.assertEqual(store.count_rows("position_snapshot"), 21)
                self.assertGreater(store.count_rows("instrument_mapping"), 0)
                self.assertEqual(store.count_rows("instrument_reference"), 160)
                batch_report = store.fetch_batch_report(
                    batch_id=first_report.batch_id,
                    engine_version=first_report.engine_version,
                )

            self.assertIsNotNone(batch_report)
            self.assertEqual(batch_report["counts"]["portfolios"], 1)
            self.assertEqual(batch_report["counts"]["books"], 5)
            self.assertEqual(batch_report["counts"]["account_portfolio_assignments"], 7)
            self.assertEqual(batch_report["counts"]["transactions"], 1025)
            self.assertEqual(batch_report["counts"]["cash_movements"], 2493)
            self.assertEqual(batch_report["counts"]["cash_balance_snapshots"], 7)
            self.assertEqual(batch_report["counts"]["accounts"], 7)
            self.assertEqual(batch_report["counts"]["account_position_snapshots"], 21)
            self.assertEqual(batch_report["counts"]["book_position_snapshots"], 21)
            self.assertEqual(batch_report["reconciliation"]["issue_count"], 2)
            self.assertEqual(batch_report["reconciliation"]["has_errors"], 0)
            self.assertEqual(len(batch_report["accounts"]), 7)
            self.assertEqual(len(batch_report["portfolios"]), 1)
            self.assertEqual(len(batch_report["books"]), 5)
            self.assertEqual(len(batch_report["account_portfolio_assignments"]), 7)
            self.assertEqual(len(batch_report["cash_balance_snapshots"]), 7)
            self.assertEqual(len(batch_report["account_position_snapshots"]), 21)
            self.assertEqual(len(batch_report["book_position_snapshots"]), 21)
            self.assertEqual(len(batch_report["position_snapshots"]), 21)

    def test_cli_persist_and_batch_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"

            persist_stdout = io.StringIO()
            with redirect_stdout(persist_stdout):
                exit_code = main(
                    [
                        "persist-status-invest-xlsx",
                        str(FIXTURE_PATH),
                        "--database",
                        str(database_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            persist_payload = json.loads(persist_stdout.getvalue())
            self.assertIn("batch_id", persist_payload)

            report_stdout = io.StringIO()
            with redirect_stdout(report_stdout):
                exit_code = main(
                    [
                        "batch-report",
                        persist_payload["batch_id"],
                        "--database",
                        str(database_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            report_payload = json.loads(report_stdout.getvalue())
            self.assertEqual(report_payload["counts"]["transactions"], 1025)
            self.assertEqual(report_payload["counts"]["books"], 5)
            self.assertEqual(report_payload["counts"]["cash_movements"], 2493)
            self.assertEqual(report_payload["counts"]["accounts"], 7)
            self.assertEqual(report_payload["reconciliation"]["issue_count"], 2)
            self.assertEqual(report_payload["reconciliation"]["has_errors"], 0)

            cash_stdout = io.StringIO()
            with redirect_stdout(cash_stdout):
                exit_code = main(
                    [
                        "cash-balances",
                        persist_payload["batch_id"],
                        "--database",
                        str(database_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            cash_payload = json.loads(cash_stdout.getvalue())
            self.assertEqual(len(cash_payload), 7)
            self.assertIn(
                "XP INVESTIMENTOS CCTVM S/A",
                {item["account_name"] for item in cash_payload},
            )

            book_stdout = io.StringIO()
            with redirect_stdout(book_stdout):
                exit_code = main(
                    [
                        "book-positions",
                        persist_payload["batch_id"],
                        "--database",
                        str(database_path),
                    ]
                )
            self.assertEqual(exit_code, 0)
            book_payload = json.loads(book_stdout.getvalue())
            self.assertEqual(len(book_payload), 21)
            self.assertIn("internacional", {item["book_id"] for item in book_payload})

    def test_persist_accepts_reference_workbook_as_config_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"

            report = persist_status_invest_xlsx(
                FIXTURE_PATH,
                database_path=database_path,
                config_path=REFERENCE_WORKBOOK_PATH,
            )

            self.assertTrue(report.config_path.endswith(".xlsx"))
            self.assertEqual(report.portfolios_loaded, 1)
            self.assertEqual(report.books_loaded, 11)
            self.assertEqual(report.account_assignments_persisted, 7)
            self.assertEqual(report.book_position_snapshots_persisted, 21)
            self.assertEqual(report.reconciliation.issue_count, 2)
            self.assertFalse(report.reconciliation.has_errors)

            with SQLiteOV10Store(database_path) as store:
                store.initialize()
                batch_report = store.fetch_batch_report(
                    batch_id=report.batch_id,
                    engine_version=report.engine_version,
                )

            self.assertIsNotNone(batch_report)
            self.assertEqual(batch_report["counts"]["books"], 11)
            self.assertEqual(batch_report["counts"]["account_position_snapshots"], 21)
            self.assertEqual(batch_report["counts"]["book_position_snapshots"], 21)
