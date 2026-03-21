from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from ov10.ingestion import load_status_invest_workbook

FIXTURE_PATH = Path("data/OV10_base_2025.xlsx")


class StatusInvestXlsxTests(unittest.TestCase):
    def test_load_status_invest_workbook_counts(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)

        self.assertTrue(bundle.batch.source_file.endswith("OV10_base_2025.xlsx"))
        self.assertEqual(len(bundle.transactions), 1025)
        self.assertEqual(len(bundle.dividend_receipts), 1486)
        self.assertEqual(len(bundle.corporate_actions), 5)

    def test_load_status_invest_workbook_maps_types(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)

        transaction_counts = Counter(item.transaction_type.value for item in bundle.transactions)
        dividend_counts = Counter(item.dividend_type.value for item in bundle.dividend_receipts)

        self.assertEqual(
            transaction_counts,
            {
                "BUY": 753,
                "SELL": 253,
                "BONUS": 9,
                "CONVERSION_IN": 5,
                "CONVERSION_OUT": 5,
            },
        )
        self.assertEqual(
            dividend_counts,
            {
                "INCOME": 813,
                "JCP": 343,
                "DIVIDEND": 328,
                "TAXABLE_INCOME": 2,
            },
        )

    def test_load_status_invest_workbook_includes_conversion_actions(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)

        first_action = bundle.corporate_actions[0]

        self.assertEqual(first_action.source_instrument_code, "VAMO3")
        self.assertEqual(first_action.target_instrument_code, "AMOB3")
        self.assertGreater(first_action.quantity_from, 0)
        self.assertGreater(first_action.quantity_to, 0)
