from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from ov10.cli import main
from ov10.fiscal import generate_fiscal_contract_report

ROOT = Path(__file__).resolve().parents[1]
SOURCE_WORKBOOK = ROOT / "data" / "OV10_base_2025.xlsx"


class FiscalContractReportTests(unittest.TestCase):
    def test_report_exposes_first_darf_and_dirpf_contracts(self) -> None:
        report = generate_fiscal_contract_report(SOURCE_WORKBOOK)
        payload = report.to_dict()

        self.assertEqual(payload["batch_id"], "status_invest_xlsx:eb06d84422c5")
        self.assertEqual(payload["snapshot_count"], 21)
        self.assertGreater(len(payload["darf"]["monthly_rows"]), 0)
        self.assertEqual(payload["dirpf"]["base_year"], 2025)
        self.assertEqual(len(payload["dirpf"]["asset_entries"]), 21)

        gap_codes = {item["code"] for item in payload["gaps"]}
        self.assertIn("missing_tax_lot_engine", gap_codes)
        self.assertIn("missing_dirpf_tax_code_mapping", gap_codes)

        section_support = {item["section_id"]: item for item in payload["dirpf"]["section_support"]}
        self.assertEqual(section_support["bens_direitos"]["support_level"], "partial")
        self.assertEqual(section_support["divida_onus"]["support_level"], "missing")
        self.assertEqual(section_support["carne_leao"]["support_level"], "missing")

    def test_cli_emits_fiscal_contract_report(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(["fiscal-contract-report", str(SOURCE_WORKBOOK)])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["batch_id"], "status_invest_xlsx:eb06d84422c5")
        self.assertEqual(payload["dirpf"]["base_year"], 2025)
