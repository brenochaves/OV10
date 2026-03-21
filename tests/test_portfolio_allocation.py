from __future__ import annotations

import unittest
from collections import Counter
from pathlib import Path

from ov10.allocation import assign_account_positions_to_books, assign_accounts_to_portfolios
from ov10.cash import build_cash_ledger
from ov10.config import load_portfolio_book_config
from ov10.ingestion import load_status_invest_workbook
from ov10.positions import compute_account_positions

CONFIG_PATH = Path("config/ov10_portfolio.toml")
FIXTURE_PATH = Path("data/OV10_base_2025.xlsx")
REFERENCE_WORKBOOK_PATH = next(Path("ov10_codex_handoff").glob("*.xlsx"))


class PortfolioAllocationTests(unittest.TestCase):
    def test_portfolio_config_assigns_accounts_and_books(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)
        cash_ledger = build_cash_ledger(bundle)
        config = load_portfolio_book_config(CONFIG_PATH)

        self.assertEqual(len(config.portfolios), 1)
        self.assertEqual(len(config.books), 5)
        self.assertEqual(config.default_portfolio_id, "core")

        account_ids_by_broker = {
            item.account_name: item.account_id for item in cash_ledger.accounts
        }
        account_positions = compute_account_positions(
            bundle.transactions,
            account_ids_by_broker=account_ids_by_broker,
        )
        account_assignments = assign_accounts_to_portfolios(
            cash_ledger.accounts,
            config,
            batch_id=bundle.batch.batch_id,
        )
        book_positions = assign_account_positions_to_books(
            account_positions,
            account_assignments,
            config,
        )

        self.assertEqual(len(account_positions), 21)
        self.assertEqual(len(account_assignments), 7)
        self.assertEqual(len(book_positions), 21)
        self.assertEqual({item.portfolio_id for item in account_assignments}, {"core"})
        self.assertEqual(
            Counter(item.book_id for item in book_positions),
            {
                "internacional": 13,
                "renda_variavel_br": 4,
                "renda_fixa": 2,
                "criptos": 2,
            },
        )

    def test_reference_workbook_config_routes_current_fixture_with_fallback_portfolio(self) -> None:
        bundle = load_status_invest_workbook(FIXTURE_PATH)
        cash_ledger = build_cash_ledger(bundle)
        config = load_portfolio_book_config(
            REFERENCE_WORKBOOK_PATH,
            fallback_path=CONFIG_PATH,
        )

        account_ids_by_broker = {
            item.account_name: item.account_id for item in cash_ledger.accounts
        }
        account_positions = compute_account_positions(
            bundle.transactions,
            account_ids_by_broker=account_ids_by_broker,
        )
        account_assignments = assign_accounts_to_portfolios(
            cash_ledger.accounts,
            config,
            batch_id=bundle.batch.batch_id,
        )
        book_positions = assign_account_positions_to_books(
            account_positions,
            account_assignments,
            config,
        )

        self.assertEqual(len(account_assignments), 7)
        self.assertEqual(len(book_positions), 21)
        self.assertEqual({item.portfolio_id for item in account_assignments}, {"core"})
        self.assertEqual(
            Counter(item.book_id for item in book_positions),
            {
                "stocks": 13,
                "acoes": 4,
                "criptos": 2,
                "tesouro_direto": 1,
                "fundos": 1,
            },
        )
