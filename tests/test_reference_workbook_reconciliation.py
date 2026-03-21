from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ov10.cli import main
from ov10.reconciliation import generate_reference_workbook_reconciliation

ROOT = Path(__file__).resolve().parents[1]
SOURCE_WORKBOOK = ROOT / "data" / "OV10_base_2025.xlsx"
REFERENCE_WORKBOOK = (
    ROOT / "ov10_codex_handoff" / "Cópia de v6.4_Controle de Investimentos (Alpha).xlsx"
)
CONFIG_PATH = ROOT / "config" / "ov10_portfolio.toml"


class ReferenceWorkbookReconciliationTests(unittest.TestCase):
    def test_report_classifies_reference_areas(self) -> None:
        report = generate_reference_workbook_reconciliation(
            SOURCE_WORKBOOK,
            reference_workbook_path=REFERENCE_WORKBOOK,
            config_path=CONFIG_PATH,
        )
        payload = report.to_dict()

        areas = {item["area_id"]: item for item in payload["areas"]}
        self.assertEqual(payload["batch_id"], "status_invest_xlsx:eb06d84422c5")
        self.assertEqual(payload["summary"]["expected_areas"], 1)
        self.assertEqual(payload["summary"]["blocking_areas"], 3)
        self.assertIn("portfolio_backend", areas)
        self.assertIn("cash_register", areas)
        self.assertIn("allocation_dashboard", areas)
        self.assertIn("income_dashboard", areas)

        portfolio_area = areas["portfolio_backend"]
        self.assertEqual(portfolio_area["overall_classification"], "blocking")
        self.assertGreaterEqual(portfolio_area["metrics"]["matched_fields"], 5)
        self.assertGreaterEqual(portfolio_area["metrics"]["blocking_fields"], 1)

        cash_area = areas["cash_register"]
        self.assertEqual(cash_area["overall_classification"], "blocking")
        cash_fields = {item["reference_field"]: item for item in cash_area["gaps"]}
        self.assertEqual(cash_fields["saldo_inicial"]["classification"], "blocking")
        self.assertEqual(cash_fields["proventos"]["support_level"], "matched")

        income_area = areas["income_dashboard"]
        self.assertEqual(income_area["overall_classification"], "expected")
        monthly_series = income_area["metrics"]["monthly_net_amounts"]
        self.assertEqual(len(monthly_series), 12)
        self.assertEqual(monthly_series[0]["month_end"], "2026-02-28")
        self.assertGreater(float(monthly_series[8]["net_amount"]), 0.0)

    def test_cli_emits_reference_reconciliation_report(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "reference-workbook-reconciliation",
                    str(SOURCE_WORKBOOK),
                    "--reference-workbook",
                    str(REFERENCE_WORKBOOK),
                    "--config",
                    str(CONFIG_PATH),
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["expected_areas"], 1)
        self.assertEqual(payload["summary"]["blocking_areas"], 3)
