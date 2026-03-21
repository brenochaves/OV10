from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

from ov10.cash import SYSTEM_ACCOUNT_ID, build_cash_ledger
from ov10.cli import main
from ov10.ingestion import load_status_invest_workbook
from ov10.testing import (
    build_synthetic_status_invest_workbook,
    generate_synthetic_status_invest_matrix,
)


class SyntheticStatusInvestTests(unittest.TestCase):
    def test_base_synthetic_workbook_roundtrips_through_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "base.xlsx"
            build_synthetic_status_invest_workbook(
                workbook_path,
                scenario_name="base",
            )

            bundle = load_status_invest_workbook(workbook_path)

        self.assertEqual(len(bundle.transactions), 3)
        self.assertEqual(len(bundle.dividend_receipts), 1)
        self.assertEqual(len(bundle.corporate_actions), 0)

    def test_legacy_unassigned_scenario_now_assigns_cash_to_unique_broker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "unassigned.xlsx"
            build_synthetic_status_invest_workbook(
                workbook_path,
                scenario_name="corporate_action_cash_unassigned",
            )

            bundle = load_status_invest_workbook(workbook_path)
            ledger = build_cash_ledger(bundle)

        balance_by_account = {item.account_id: item.balance for item in ledger.balance_snapshots}
        self.assertNotIn(SYSTEM_ACCOUNT_ID, balance_by_account)
        self.assertEqual(len(ledger.corporate_action_resolutions), 1)
        self.assertEqual(ledger.corporate_action_resolutions[0].reason, "conversion_broker_match")
        self.assertEqual(next(iter(balance_by_account.values())), Decimal("-987.50"))

    def test_ambiguous_corporate_action_scenario_uses_system_account(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "ambiguous.xlsx"
            build_synthetic_status_invest_workbook(
                workbook_path,
                scenario_name="corporate_action_cash_ambiguous",
            )

            bundle = load_status_invest_workbook(workbook_path)
            ledger = build_cash_ledger(bundle)

        balance_by_account = {item.account_id: item.balance for item in ledger.balance_snapshots}
        self.assertIn(SYSTEM_ACCOUNT_ID, balance_by_account)
        self.assertEqual(balance_by_account[SYSTEM_ACCOUNT_ID], Decimal("3.25"))
        self.assertEqual(len(ledger.corporate_action_resolutions), 1)
        self.assertEqual(
            ledger.corporate_action_resolutions[0].reason,
            "ambiguous_candidate_brokers",
        )

    def test_generate_scenario_matrix_creates_all_known_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            reports = generate_synthetic_status_invest_matrix(temp_dir)

            generated_paths = {Path(item["output_path"]).name for item in reports}

        self.assertEqual(
            generated_paths,
            {
                "base.xlsx",
                "corporate_action_cash_ambiguous.xlsx",
                "corporate_action_cash_unassigned.xlsx",
            },
        )

    def test_cli_generates_synthetic_workbook(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workbook_path = Path(temp_dir) / "cli_base.xlsx"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "generate-synthetic-status-invest-xlsx",
                        str(workbook_path),
                        "--scenario",
                        "base",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertTrue(workbook_path.exists())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["scenario"], "base")
        self.assertEqual(payload["transactions"], 3)
