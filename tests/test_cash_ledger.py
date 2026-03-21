from __future__ import annotations

import unittest
from decimal import Decimal
from pathlib import Path

from ov10.cash import SYSTEM_ACCOUNT_NAME, build_cash_ledger
from ov10.ingestion import load_status_invest_workbook

FIXTURE_PATH = Path("data/OV10_base_2025.xlsx")


class CashLedgerTests(unittest.TestCase):
    def test_build_cash_ledger_derives_accounts_movements_and_balances(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)
        ledger = build_cash_ledger(bundle)

        self.assertEqual(len(ledger.accounts), 7)
        self.assertEqual(len(ledger.movements), 2493)
        self.assertEqual(len(ledger.balance_snapshots), 7)
        self.assertEqual(len(ledger.corporate_action_resolutions), 1)

        account_ids_by_name = {item.account_name: item.account_id for item in ledger.accounts}
        self.assertNotIn(SYSTEM_ACCOUNT_NAME, account_ids_by_name)

        balance_by_account_id = {item.account_id: item.balance for item in ledger.balance_snapshots}
        self.assertEqual(
            balance_by_account_id[account_ids_by_name["INTER DTVM LTDA"]],
            Decimal("13024.12"),
        )
        self.assertEqual(sum(balance_by_account_id.values(), Decimal("0")), Decimal("-1854.24"))
        resolution = ledger.corporate_action_resolutions[0]
        self.assertEqual(resolution.account_name, "INTER DTVM LTDA")
        self.assertEqual(resolution.reason, "conversion_broker_match")
        self.assertEqual(resolution.candidate_brokers, ("INTER DTVM LTDA",))
