from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from ov10.cli import main
from ov10.ingestion import load_status_invest_workbook
from ov10.market.models import MarketSnapshot
from ov10.positions import compute_positions
from ov10.reconciliation import generate_reference_workbook_reconciliation
from ov10.services import persist_status_invest_xlsx
from ov10.storage import SQLiteOV10Store

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

    def test_report_consumes_persisted_market_snapshots_when_database_is_provided(self) -> None:
        bundle = load_status_invest_workbook(SOURCE_WORKBOOK)
        positions = compute_positions(bundle.transactions)
        self.assertGreater(len(positions), 0)

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "ov10.sqlite3"
            persist_status_invest_xlsx(
                SOURCE_WORKBOOK,
                database_path=database_path,
                config_path=CONFIG_PATH,
            )
            market_snapshots = [
                MarketSnapshot(
                    canonical_code=item.instrument_code,
                    provider_name="stub_market",
                    source_symbol=item.instrument_code,
                    snapshot_date=item.snapshot_date,
                    observed_at=datetime(2026, 3, 20, 21, 0, tzinfo=UTC),
                    retrieved_at=datetime(2026, 3, 20, 21, 1, tzinfo=UTC),
                    currency=item.currency,
                    price=item.avg_cost + Decimal("1"),
                    previous_close=item.avg_cost,
                    absolute_change=Decimal("1"),
                    percent_change=Decimal("1"),
                    market="B3",
                    provider_metadata_json=json.dumps({"longName": f"{item.instrument_code} SA"}),
                )
                for item in positions
            ]
            with SQLiteOV10Store(database_path) as store:
                store.initialize()
                store.upsert_market_snapshots(market_snapshots)

            baseline_report = generate_reference_workbook_reconciliation(
                SOURCE_WORKBOOK,
                reference_workbook_path=REFERENCE_WORKBOOK,
                config_path=CONFIG_PATH,
            ).to_dict()
            enriched_report = generate_reference_workbook_reconciliation(
                SOURCE_WORKBOOK,
                reference_workbook_path=REFERENCE_WORKBOOK,
                config_path=CONFIG_PATH,
                database_path=database_path,
            ).to_dict()

        self.assertEqual(baseline_report["summary"]["blocking_areas"], 3)
        self.assertEqual(enriched_report["summary"]["blocking_areas"], 3)

        baseline_areas = {item["area_id"]: item for item in baseline_report["areas"]}
        enriched_areas = {item["area_id"]: item for item in enriched_report["areas"]}

        portfolio_before = baseline_areas["portfolio_backend"]
        portfolio_after = enriched_areas["portfolio_backend"]
        self.assertLess(
            portfolio_after["metrics"]["blocking_fields"],
            portfolio_before["metrics"]["blocking_fields"],
        )
        portfolio_gaps = {item["reference_field"]: item for item in portfolio_after["gaps"]}
        self.assertEqual(portfolio_gaps["market_cod"]["classification"], "expected")
        self.assertEqual(portfolio_gaps["nome_pregao"]["classification"], "expected")
        self.assertEqual(portfolio_gaps["price"]["classification"], "expected")
        self.assertEqual(portfolio_gaps["pm_fx"]["classification"], "expected")
        self.assertEqual(portfolio_gaps["moeda_price"]["classification"], "expected")

        allocation_before = baseline_areas["allocation_dashboard"]
        allocation_after = enriched_areas["allocation_dashboard"]
        self.assertLess(
            allocation_after["metrics"]["blocking_fields"],
            allocation_before["metrics"]["blocking_fields"],
        )
        allocation_gaps = {item["reference_field"]: item for item in allocation_after["gaps"]}
        self.assertEqual(allocation_gaps["VALOR DE MERCADO"]["classification"], "expected")
        self.assertEqual(allocation_gaps["LUCRO TOTAL"]["classification"], "expected")
        self.assertEqual(allocation_gaps["%"]["classification"], "expected")
