from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TypedDict

from ov10.domain.models import (
    AccountPortfolioAssignment,
    AccountPositionSnapshot,
    AccountRegistryEntry,
    BookDefinition,
    BookPositionSnapshot,
    CanonicalCorporateAction,
    CanonicalDividendReceipt,
    CanonicalTransaction,
    CashBalanceSnapshot,
    CashMovement,
    ImportBatch,
    IngestionBundle,
    PortfolioDefinition,
    PositionSnapshot,
    SourceRecord,
)
from ov10.market.models import FxSnapshot, MarketSnapshot
from ov10.reference import InstrumentReference

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_SQL_PATH = REPO_ROOT / "sql" / "schema.sql"
SCHEMA_SQL = SCHEMA_SQL_PATH.read_text(encoding="utf-8")


class _BatchReconciliationPayload(TypedDict):
    transaction_count: int
    dividend_receipt_count: int
    corporate_action_count: int
    source_record_count: int
    mapping_count: int
    snapshot_count: int
    issue_count: int
    has_errors: bool
    issues: list[dict[str, object]]
    created_at: datetime


def initialize_database(path: str | Path) -> Path:
    database_path = Path(path)
    with SQLiteOV10Store(database_path) as store:
        store.initialize()
    return database_path


class SQLiteOV10Store:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def __enter__(self) -> SQLiteOV10Store:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

    def initialize(self) -> None:
        self.connection.executescript(SCHEMA_SQL)
        self.connection.commit()

    def persist_ingestion_bundle(self, bundle: IngestionBundle) -> dict[str, int | bool]:
        with self.connection:
            batch_created = self._insert_import_batch(bundle.batch)
            source_records_inserted = self._insert_source_records(bundle)
            transactions_inserted = self._insert_transactions(bundle.transactions)
            dividend_receipts_inserted = self._insert_dividend_receipts(bundle.dividend_receipts)
            corporate_actions_inserted = self._insert_corporate_actions(bundle.corporate_actions)

        return {
            "batch_created": batch_created,
            "source_records_inserted": source_records_inserted,
            "transactions_inserted": transactions_inserted,
            "dividend_receipts_inserted": dividend_receipts_inserted,
            "corporate_actions_inserted": corporate_actions_inserted,
        }

    def upsert_instrument_mappings(
        self,
        *,
        batch_id: str,
        mappings: list[dict[str, str]],
    ) -> int:
        sql = """
            INSERT INTO instrument_mapping (
                mapping_id,
                source_system,
                source_code,
                canonical_code,
                instrument_type,
                mapping_origin,
                first_batch_id,
                last_batch_id,
                notes,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_system, source_code) DO UPDATE SET
                canonical_code = excluded.canonical_code,
                instrument_type = CASE
                    WHEN instrument_mapping.instrument_type = 'unknown'
                        AND excluded.instrument_type <> 'unknown'
                    THEN excluded.instrument_type
                    ELSE instrument_mapping.instrument_type
                END,
                last_batch_id = excluded.last_batch_id,
                mapping_origin = instrument_mapping.mapping_origin,
                notes = COALESCE(instrument_mapping.notes, excluded.notes),
                is_active = 1
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item["mapping_id"],
                        item["source_system"],
                        item["source_code"],
                        item["canonical_code"],
                        item["instrument_type"],
                        item["mapping_origin"],
                        item["first_batch_id"],
                        batch_id,
                        item["notes"],
                        1,
                    )
                    for item in mappings
                ],
            )
        return len(mappings)

    def upsert_instrument_references(self, references: list[InstrumentReference]) -> int:
        sql = """
            INSERT INTO instrument_reference (
                canonical_code,
                instrument_type,
                asset_category,
                currency,
                reference_origin,
                identity_status,
                first_batch_id,
                last_batch_id,
                notes,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_code) DO UPDATE SET
                instrument_type = CASE
                    WHEN excluded.instrument_type <> 'unknown'
                    THEN excluded.instrument_type
                    ELSE instrument_reference.instrument_type
                END,
                asset_category = CASE
                    WHEN excluded.asset_category <> 'unknown'
                    THEN excluded.asset_category
                    ELSE instrument_reference.asset_category
                END,
                currency = excluded.currency,
                reference_origin = excluded.reference_origin,
                identity_status = CASE
                    WHEN instrument_reference.identity_status = 'observed_with_conflict'
                    THEN instrument_reference.identity_status
                    WHEN excluded.identity_status = 'observed_with_conflict'
                    THEN excluded.identity_status
                    WHEN excluded.identity_status = 'observed_identity'
                    THEN excluded.identity_status
                    ELSE instrument_reference.identity_status
                END,
                last_batch_id = excluded.last_batch_id,
                notes = excluded.notes,
                is_active = excluded.is_active
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.canonical_code,
                        item.instrument_type.value,
                        item.asset_category,
                        item.currency,
                        item.reference_origin,
                        item.identity_status,
                        item.first_batch_id,
                        item.last_batch_id,
                        item.notes,
                        1 if item.is_active else 0,
                    )
                    for item in references
                ],
            )
        return len(references)

    def upsert_market_snapshots(self, snapshots: list[MarketSnapshot]) -> int:
        sql = """
            INSERT INTO market_snapshot (
                provider_name,
                canonical_code,
                source_symbol,
                snapshot_date,
                observed_at,
                retrieved_at,
                currency,
                price,
                previous_close,
                absolute_change,
                percent_change,
                market,
                quote_status,
                provider_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider_name, canonical_code, snapshot_date) DO UPDATE SET
                source_symbol = excluded.source_symbol,
                observed_at = excluded.observed_at,
                retrieved_at = excluded.retrieved_at,
                currency = excluded.currency,
                price = excluded.price,
                previous_close = excluded.previous_close,
                absolute_change = excluded.absolute_change,
                percent_change = excluded.percent_change,
                market = excluded.market,
                quote_status = excluded.quote_status,
                provider_metadata_json = excluded.provider_metadata_json
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.provider_name,
                        item.canonical_code,
                        item.source_symbol,
                        item.snapshot_date.isoformat(),
                        item.observed_at.isoformat(),
                        item.retrieved_at.isoformat(),
                        item.currency,
                        _decimal_str(item.price),
                        _decimal_str(item.previous_close),
                        _decimal_str(item.absolute_change),
                        _decimal_str(item.percent_change),
                        item.market,
                        item.quote_status,
                        item.provider_metadata_json,
                    )
                    for item in snapshots
                ],
            )
        return len(snapshots)

    def upsert_fx_snapshots(self, snapshots: list[FxSnapshot]) -> int:
        sql = """
            INSERT INTO fx_snapshot (
                provider_name,
                base_currency,
                quote_currency,
                snapshot_date,
                observed_at,
                retrieved_at,
                rate,
                rate_kind,
                bid,
                ask,
                bulletin_type,
                provider_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider_name, base_currency, quote_currency, snapshot_date) DO UPDATE SET
                observed_at = excluded.observed_at,
                retrieved_at = excluded.retrieved_at,
                rate = excluded.rate,
                rate_kind = excluded.rate_kind,
                bid = excluded.bid,
                ask = excluded.ask,
                bulletin_type = excluded.bulletin_type,
                provider_metadata_json = excluded.provider_metadata_json
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.provider_name,
                        item.base_currency,
                        item.quote_currency,
                        item.snapshot_date.isoformat(),
                        item.observed_at.isoformat(),
                        item.retrieved_at.isoformat(),
                        _decimal_str(item.rate),
                        item.rate_kind,
                        _decimal_str(item.bid),
                        _decimal_str(item.ask),
                        item.bulletin_type,
                        item.provider_metadata_json,
                    )
                    for item in snapshots
                ],
            )
        return len(snapshots)

    def upsert_accounts(self, accounts: list[AccountRegistryEntry]) -> int:
        sql = """
            INSERT INTO account_registry (
                account_id,
                source_system,
                account_type,
                account_name,
                first_batch_id,
                last_batch_id,
                currency,
                is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                last_batch_id = excluded.last_batch_id,
                currency = excluded.currency,
                is_active = 1
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.account_id,
                        item.source_system.value,
                        item.account_type.value,
                        item.account_name,
                        item.first_batch_id,
                        item.last_batch_id,
                        item.currency,
                        1,
                    )
                    for item in accounts
                ],
            )
        return len(accounts)

    def upsert_portfolios(self, portfolios: list[PortfolioDefinition]) -> int:
        sql = """
            INSERT INTO portfolio_registry (
                portfolio_id,
                name,
                short_name,
                profile,
                is_active
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(portfolio_id) DO UPDATE SET
                name = excluded.name,
                short_name = excluded.short_name,
                profile = excluded.profile,
                is_active = excluded.is_active
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.portfolio_id,
                        item.name,
                        item.short_name,
                        item.profile,
                        1 if item.is_active else 0,
                    )
                    for item in portfolios
                ],
            )
        return len(portfolios)

    def upsert_books(self, books: list[BookDefinition]) -> int:
        sql = """
            INSERT INTO book_registry (
                book_id,
                portfolio_id,
                name,
                target_weight,
                instrument_types_json,
                is_active,
                sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(book_id) DO UPDATE SET
                portfolio_id = excluded.portfolio_id,
                name = excluded.name,
                target_weight = excluded.target_weight,
                instrument_types_json = excluded.instrument_types_json,
                is_active = excluded.is_active,
                sort_order = excluded.sort_order
        """
        with self.connection:
            self.connection.executemany(
                sql,
                [
                    (
                        item.book_id,
                        item.portfolio_id,
                        item.name,
                        _decimal_str(item.target_weight),
                        json.dumps([value.value for value in item.instrument_types]),
                        1 if item.is_active else 0,
                        item.sort_order,
                    )
                    for item in books
                ],
            )
        return len(books)

    def replace_account_portfolio_assignments(
        self,
        *,
        batch_id: str,
        assignments: list[AccountPortfolioAssignment],
    ) -> int:
        with self.connection:
            self.connection.execute(
                "DELETE FROM account_portfolio_assignment WHERE batch_id = ?",
                (batch_id,),
            )
            self.connection.executemany(
                """
                INSERT INTO account_portfolio_assignment (
                    batch_id,
                    account_id,
                    portfolio_id
                ) VALUES (?, ?, ?)
                """,
                [
                    (
                        item.batch_id,
                        item.account_id,
                        item.portfolio_id,
                    )
                    for item in assignments
                ],
            )
        return len(assignments)

    def replace_cash_movements(self, *, batch_id: str, movements: list[CashMovement]) -> int:
        with self.connection:
            self.connection.execute(
                "DELETE FROM cash_movement WHERE batch_id = ?",
                (batch_id,),
            )
            self.connection.executemany(
                """
                INSERT INTO cash_movement (
                    movement_id,
                    batch_id,
                    account_id,
                    movement_date,
                    movement_type,
                    amount,
                    currency,
                    related_record_type,
                    related_record_id,
                    instrument_code,
                    description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.movement_id,
                        item.batch_id,
                        item.account_id,
                        item.movement_date.isoformat(),
                        item.movement_type.value,
                        _decimal_str(item.amount),
                        item.currency,
                        item.related_record_type,
                        item.related_record_id,
                        item.instrument_code,
                        item.description,
                    )
                    for item in movements
                ],
            )
        return len(movements)

    def replace_cash_balance_snapshots(
        self,
        *,
        batch_id: str,
        snapshots: list[CashBalanceSnapshot],
    ) -> int:
        with self.connection:
            self.connection.execute(
                "DELETE FROM cash_balance_snapshot WHERE batch_id = ?",
                (batch_id,),
            )
            self.connection.executemany(
                """
                INSERT INTO cash_balance_snapshot (
                    batch_id,
                    snapshot_date,
                    account_id,
                    currency,
                    balance
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item.batch_id,
                        item.snapshot_date.isoformat(),
                        item.account_id,
                        item.currency,
                        _decimal_str(item.balance),
                    )
                    for item in snapshots
                ],
            )
        return len(snapshots)

    def replace_account_position_snapshots(
        self,
        *,
        batch_id: str,
        engine_version: str,
        snapshots: list[AccountPositionSnapshot],
    ) -> int:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM account_position_snapshot
                WHERE batch_id = ? AND engine_version = ?
                """,
                (batch_id, engine_version),
            )
            self.connection.executemany(
                """
                INSERT INTO account_position_snapshot (
                    batch_id,
                    snapshot_date,
                    account_id,
                    instrument_code,
                    instrument_type,
                    quantity,
                    total_cost,
                    avg_cost,
                    currency,
                    engine_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        batch_id,
                        item.snapshot_date.isoformat(),
                        item.account_id,
                        item.instrument_code,
                        item.instrument_type.value,
                        _decimal_str(item.quantity),
                        _decimal_str(item.total_cost),
                        _decimal_str(item.avg_cost),
                        item.currency,
                        item.engine_version,
                    )
                    for item in snapshots
                ],
            )
        return len(snapshots)

    def replace_book_position_snapshots(
        self,
        *,
        batch_id: str,
        engine_version: str,
        snapshots: list[BookPositionSnapshot],
    ) -> int:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM book_position_snapshot
                WHERE batch_id = ? AND engine_version = ?
                """,
                (batch_id, engine_version),
            )
            self.connection.executemany(
                """
                INSERT INTO book_position_snapshot (
                    batch_id,
                    snapshot_date,
                    portfolio_id,
                    book_id,
                    account_id,
                    instrument_code,
                    instrument_type,
                    quantity,
                    total_cost,
                    avg_cost,
                    currency,
                    engine_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        batch_id,
                        item.snapshot_date.isoformat(),
                        item.portfolio_id,
                        item.book_id,
                        item.account_id,
                        item.instrument_code,
                        item.instrument_type.value,
                        _decimal_str(item.quantity),
                        _decimal_str(item.total_cost),
                        _decimal_str(item.avg_cost),
                        item.currency,
                        item.engine_version,
                    )
                    for item in snapshots
                ],
            )
        return len(snapshots)

    def replace_position_snapshots(
        self,
        *,
        batch_id: str,
        engine_version: str,
        snapshots: list[PositionSnapshot],
    ) -> int:
        with self.connection:
            self.connection.execute(
                "DELETE FROM position_snapshot WHERE batch_id = ? AND engine_version = ?",
                (batch_id, engine_version),
            )
            self.connection.executemany(
                """
                INSERT INTO position_snapshot (
                    batch_id,
                    snapshot_date,
                    instrument_code,
                    instrument_type,
                    quantity,
                    total_cost,
                    avg_cost,
                    currency,
                    engine_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        batch_id,
                        snapshot.snapshot_date.isoformat(),
                        snapshot.instrument_code,
                        snapshot.instrument_type.value,
                        _decimal_str(snapshot.quantity),
                        _decimal_str(snapshot.total_cost),
                        _decimal_str(snapshot.avg_cost),
                        snapshot.currency,
                        snapshot.engine_version,
                    )
                    for snapshot in snapshots
                ],
            )
        return len(snapshots)

    def replace_batch_reconciliation(
        self,
        *,
        batch_id: str,
        engine_version: str,
        report: _BatchReconciliationPayload,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT OR REPLACE INTO batch_reconciliation (
                    batch_id,
                    engine_version,
                    transaction_count,
                    dividend_receipt_count,
                    corporate_action_count,
                    source_record_count,
                    mapping_count,
                    snapshot_count,
                    issue_count,
                    has_errors,
                    issues_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    engine_version,
                    report["transaction_count"],
                    report["dividend_receipt_count"],
                    report["corporate_action_count"],
                    report["source_record_count"],
                    report["mapping_count"],
                    report["snapshot_count"],
                    report["issue_count"],
                    1 if report["has_errors"] else 0,
                    json.dumps(report["issues"], sort_keys=True),
                    _datetime_str(report["created_at"]),
                ),
            )

    def fetch_batch_report(self, *, batch_id: str, engine_version: str) -> dict[str, object] | None:
        batch_row = self.connection.execute(
            """
            SELECT batch_id, source_system, source_file, file_sha256, imported_at
            FROM import_batch
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()
        if batch_row is None:
            return None

        reconciliation_row = self.connection.execute(
            """
            SELECT *
            FROM batch_reconciliation
            WHERE batch_id = ? AND engine_version = ?
            """,
            (batch_id, engine_version),
        ).fetchone()

        snapshot_rows = self.connection.execute(
            """
            SELECT snapshot_date, instrument_code, instrument_type, quantity, total_cost, avg_cost,
                   currency, engine_version
            FROM position_snapshot
            WHERE batch_id = ? AND engine_version = ?
            ORDER BY instrument_code
            """,
            (batch_id, engine_version),
        ).fetchall()

        cash_balance_rows = self.connection.execute(
            """
            SELECT snapshot_date, account_id, currency, balance
            FROM cash_balance_snapshot
            WHERE batch_id = ?
            ORDER BY account_id
            """,
            (batch_id,),
        ).fetchall()

        account_rows = self.connection.execute(
            """
            SELECT account_id, source_system, account_type, account_name, currency
            FROM account_registry
            WHERE account_id IN (
                SELECT DISTINCT account_id
                FROM cash_movement
                WHERE batch_id = ?
            )
            ORDER BY account_name
            """,
            (batch_id,),
        ).fetchall()

        portfolio_rows = self.connection.execute(
            """
            SELECT DISTINCT
                portfolio_registry.portfolio_id,
                portfolio_registry.name,
                portfolio_registry.short_name,
                portfolio_registry.profile,
                portfolio_registry.is_active
            FROM portfolio_registry
            INNER JOIN account_portfolio_assignment
                ON account_portfolio_assignment.portfolio_id = portfolio_registry.portfolio_id
            WHERE account_portfolio_assignment.batch_id = ?
            ORDER BY portfolio_registry.portfolio_id
            """,
            (batch_id,),
        ).fetchall()

        book_rows = self.connection.execute(
            """
            SELECT
                book_registry.book_id,
                book_registry.portfolio_id,
                book_registry.name,
                book_registry.target_weight,
                book_registry.instrument_types_json,
                book_registry.is_active,
                book_registry.sort_order
            FROM book_registry
            WHERE book_registry.portfolio_id IN (
                SELECT DISTINCT portfolio_id
                FROM account_portfolio_assignment
                WHERE batch_id = ?
            )
            ORDER BY book_registry.portfolio_id, book_registry.sort_order, book_registry.book_id
            """,
            (batch_id,),
        ).fetchall()

        account_assignment_rows = self.connection.execute(
            """
            SELECT batch_id, account_id, portfolio_id
            FROM account_portfolio_assignment
            WHERE batch_id = ?
            ORDER BY account_id
            """,
            (batch_id,),
        ).fetchall()

        account_position_rows = self.connection.execute(
            """
            SELECT
                account_id,
                snapshot_date,
                instrument_code,
                instrument_type,
                quantity,
                total_cost,
                avg_cost,
                currency,
                engine_version
            FROM account_position_snapshot
            WHERE batch_id = ? AND engine_version = ?
            ORDER BY account_id, instrument_code
            """,
            (batch_id, engine_version),
        ).fetchall()

        book_position_rows = self.connection.execute(
            """
            SELECT
                portfolio_id,
                book_id,
                account_id,
                snapshot_date,
                instrument_code,
                instrument_type,
                quantity,
                total_cost,
                avg_cost,
                currency,
                engine_version
            FROM book_position_snapshot
            WHERE batch_id = ? AND engine_version = ?
            ORDER BY portfolio_id, book_id, account_id, instrument_code
            """,
            (batch_id, engine_version),
        ).fetchall()

        counts = {
            "portfolios": len(portfolio_rows),
            "books": len(book_rows),
            "account_portfolio_assignments": self.count_rows(
                "account_portfolio_assignment",
                batch_id=batch_id,
            ),
            "source_records": self.count_rows("source_record", batch_id=batch_id),
            "transactions": self.count_rows("canonical_transaction", batch_id=batch_id),
            "dividend_receipts": self.count_rows("canonical_dividend_receipt", batch_id=batch_id),
            "corporate_actions": self.count_rows("canonical_corporate_action", batch_id=batch_id),
            "cash_movements": self.count_rows("cash_movement", batch_id=batch_id),
            "cash_balance_snapshots": self.count_rows("cash_balance_snapshot", batch_id=batch_id),
            "accounts": len(account_rows),
            "account_position_snapshots": self.count_rows(
                "account_position_snapshot",
                batch_id=batch_id,
            ),
            "book_position_snapshots": self.count_rows(
                "book_position_snapshot",
                batch_id=batch_id,
            ),
        }

        payload: dict[str, object] = {
            "batch": dict(batch_row),
            "counts": counts,
            "accounts": [dict(row) for row in account_rows],
            "portfolios": [dict(row) for row in portfolio_rows],
            "books": [
                {
                    **dict(row),
                    "instrument_types": json.loads(row["instrument_types_json"]),
                }
                for row in book_rows
            ],
            "account_portfolio_assignments": [dict(row) for row in account_assignment_rows],
            "cash_balance_snapshots": [dict(row) for row in cash_balance_rows],
            "account_position_snapshots": [dict(row) for row in account_position_rows],
            "book_position_snapshots": [dict(row) for row in book_position_rows],
            "position_snapshots": [dict(row) for row in snapshot_rows],
        }
        if reconciliation_row is not None:
            reconciliation = dict(reconciliation_row)
            reconciliation["issues"] = json.loads(reconciliation.pop("issues_json"))
            payload["reconciliation"] = reconciliation

        return payload

    def list_batches(self, *, engine_version: str) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT
                import_batch.batch_id,
                import_batch.source_system,
                import_batch.source_file,
                import_batch.imported_at,
                COALESCE(batch_reconciliation.issue_count, 0) AS issue_count,
                COALESCE(batch_reconciliation.has_errors, 0) AS has_errors
            FROM import_batch
            LEFT JOIN batch_reconciliation
                ON batch_reconciliation.batch_id = import_batch.batch_id
               AND batch_reconciliation.engine_version = ?
            ORDER BY import_batch.imported_at DESC
            """,
            (engine_version,),
        ).fetchall()
        return [dict(row) for row in rows]

    def fetch_instrument_reference_report(
        self,
        *,
        batch_id: str | None = None,
    ) -> dict[str, object]:
        reference_rows = self.connection.execute(
            """
            SELECT
                canonical_code,
                instrument_type,
                asset_category,
                currency,
                reference_origin,
                identity_status,
                first_batch_id,
                last_batch_id,
                notes,
                is_active
            FROM instrument_reference
            WHERE is_active = 1
            ORDER BY canonical_code
            """
        ).fetchall()
        alias_rows = self.connection.execute(
            """
            SELECT
                canonical_code,
                source_system,
                source_code,
                instrument_type,
                mapping_origin,
                first_batch_id,
                last_batch_id,
                notes,
                is_active
            FROM instrument_mapping
            WHERE is_active = 1
            ORDER BY canonical_code, source_system, source_code
            """
        ).fetchall()
        alias_by_canonical: dict[str, list[dict[str, object]]] = {}
        for row in alias_rows:
            alias_by_canonical.setdefault(row["canonical_code"], []).append(dict(row))

        transaction_counts = self._fetch_group_counts(
            table_name="canonical_transaction",
            code_column="instrument_code",
            batch_id=batch_id,
        )
        dividend_counts = self._fetch_group_counts(
            table_name="canonical_dividend_receipt",
            code_column="instrument_code",
            batch_id=batch_id,
        )
        corporate_action_source_counts = self._fetch_group_counts(
            table_name="canonical_corporate_action",
            code_column="source_instrument_code",
            batch_id=batch_id,
        )
        corporate_action_target_counts = self._fetch_group_counts(
            table_name="canonical_corporate_action",
            code_column="target_instrument_code",
            batch_id=batch_id,
        )

        references = []
        status_counts: dict[str, int] = {}
        for row in reference_rows:
            item = dict(row)
            status = item["identity_status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            canonical_code = item["canonical_code"]
            aliases = alias_by_canonical.get(canonical_code, [])
            item["alias_count"] = len(aliases)
            item["aliases"] = aliases
            item["observation_counts"] = {
                "transactions": transaction_counts.get(canonical_code, 0),
                "dividend_receipts": dividend_counts.get(canonical_code, 0),
                "corporate_action_sources": corporate_action_source_counts.get(canonical_code, 0),
                "corporate_action_targets": corporate_action_target_counts.get(canonical_code, 0),
            }
            references.append(item)

        return {
            "batch_id": batch_id,
            "counts": {
                "instrument_references": len(references),
                "instrument_aliases": len(alias_rows),
                "identity_statuses": status_counts,
            },
            "references": references,
        }

    def list_active_instrument_references(self) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT
                canonical_code,
                instrument_type,
                asset_category,
                currency,
                reference_origin,
                identity_status,
                first_batch_id,
                last_batch_id,
                notes,
                is_active
            FROM instrument_reference
            WHERE is_active = 1
            ORDER BY canonical_code
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def fetch_market_snapshot_report(
        self,
        *,
        canonical_code: str | None = None,
        provider_name: str | None = None,
    ) -> dict[str, object]:
        where_clauses: list[str] = []
        parameters: list[str] = []
        if canonical_code is not None:
            where_clauses.append("canonical_code = ?")
            parameters.append(canonical_code.strip().upper())
        if provider_name is not None:
            where_clauses.append("provider_name = ?")
            parameters.append(provider_name.strip())

        sql = """
            SELECT
                provider_name,
                canonical_code,
                source_symbol,
                snapshot_date,
                observed_at,
                retrieved_at,
                currency,
                price,
                previous_close,
                absolute_change,
                percent_change,
                market,
                quote_status,
                provider_metadata_json
            FROM market_snapshot
        """
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY snapshot_date DESC, canonical_code, provider_name"

        rows = self.connection.execute(sql, parameters).fetchall()
        snapshots = [_deserialize_market_snapshot_row(row) for row in rows]
        latest_by_code: dict[str, dict[str, object]] = {}
        provider_counts: dict[str, int] = {}
        for item in snapshots:
            latest_by_code.setdefault(str(item["canonical_code"]), item)
            provider = str(item["provider_name"])
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "filters": {
                "canonical_code": canonical_code,
                "provider_name": provider_name,
            },
            "counts": {
                "snapshots": len(snapshots),
                "latest_snapshots": len(latest_by_code),
                "providers": provider_counts,
            },
            "latest_snapshots": list(latest_by_code.values()),
            "snapshots": snapshots,
        }

    def fetch_latest_market_snapshots(
        self,
        *,
        canonical_codes: list[str] | tuple[str, ...],
        as_of_date: date | None = None,
        provider_name: str | None = None,
    ) -> dict[str, dict[str, object]]:
        normalized_codes = sorted(
            {item.strip().upper() for item in canonical_codes if item.strip()}
        )
        if not normalized_codes:
            return {}

        placeholders = ", ".join("?" for _ in normalized_codes)
        parameters: list[str] = list(normalized_codes)
        where_clauses = [f"canonical_code IN ({placeholders})"]
        if as_of_date is not None:
            where_clauses.append("snapshot_date <= ?")
            parameters.append(as_of_date.isoformat())
        if provider_name is not None:
            where_clauses.append("provider_name = ?")
            parameters.append(provider_name.strip())

        sql = """
            SELECT
                provider_name,
                canonical_code,
                source_symbol,
                snapshot_date,
                observed_at,
                retrieved_at,
                currency,
                price,
                previous_close,
                absolute_change,
                percent_change,
                market,
                quote_status,
                provider_metadata_json
            FROM market_snapshot
            WHERE
        """
        sql += " AND ".join(where_clauses)
        sql += " ORDER BY canonical_code, snapshot_date DESC, observed_at DESC, provider_name"

        rows = self.connection.execute(sql, parameters).fetchall()
        payload: dict[str, dict[str, object]] = {}
        for row in rows:
            item = _deserialize_market_snapshot_row(row)
            payload.setdefault(str(item["canonical_code"]), item)
        return payload

    def fetch_fx_snapshot_report(
        self,
        *,
        base_currency: str | None = None,
        quote_currency: str | None = None,
        provider_name: str | None = None,
    ) -> dict[str, object]:
        where_clauses: list[str] = []
        parameters: list[str] = []
        if base_currency is not None:
            where_clauses.append("base_currency = ?")
            parameters.append(base_currency.strip().upper())
        if quote_currency is not None:
            where_clauses.append("quote_currency = ?")
            parameters.append(quote_currency.strip().upper())
        if provider_name is not None:
            where_clauses.append("provider_name = ?")
            parameters.append(provider_name.strip())

        sql = """
            SELECT
                provider_name,
                base_currency,
                quote_currency,
                snapshot_date,
                observed_at,
                retrieved_at,
                rate,
                rate_kind,
                bid,
                ask,
                bulletin_type,
                provider_metadata_json
            FROM fx_snapshot
        """
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        sql += " ORDER BY snapshot_date DESC, base_currency, quote_currency, provider_name"

        rows = self.connection.execute(sql, parameters).fetchall()
        snapshots = [_deserialize_fx_snapshot_row(row) for row in rows]
        latest_by_pair: dict[tuple[str, str], dict[str, object]] = {}
        provider_counts: dict[str, int] = {}
        for item in snapshots:
            pair_key = (str(item["base_currency"]), str(item["quote_currency"]))
            latest_by_pair.setdefault(pair_key, item)
            provider = str(item["provider_name"])
            provider_counts[provider] = provider_counts.get(provider, 0) + 1

        return {
            "filters": {
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "provider_name": provider_name,
            },
            "counts": {
                "snapshots": len(snapshots),
                "latest_pairs": len(latest_by_pair),
                "providers": provider_counts,
            },
            "latest_snapshots": list(latest_by_pair.values()),
            "snapshots": snapshots,
        }

    def fetch_latest_fx_snapshots(
        self,
        *,
        currencies: list[str] | tuple[str, ...],
        as_of_date: date | None = None,
        provider_name: str | None = None,
    ) -> dict[tuple[str, str], dict[str, object]]:
        normalized_currencies = sorted(
            {item.strip().upper() for item in currencies if item.strip()}
        )
        if not normalized_currencies:
            return {}

        placeholders = ", ".join("?" for _ in normalized_currencies)
        parameters: list[str] = list(normalized_currencies) + list(normalized_currencies)
        where_clauses = [
            f"(base_currency IN ({placeholders}) OR quote_currency IN ({placeholders}))"
        ]
        if as_of_date is not None:
            where_clauses.append("snapshot_date <= ?")
            parameters.append(as_of_date.isoformat())
        if provider_name is not None:
            where_clauses.append("provider_name = ?")
            parameters.append(provider_name.strip())

        sql = """
            SELECT
                provider_name,
                base_currency,
                quote_currency,
                snapshot_date,
                observed_at,
                retrieved_at,
                rate,
                rate_kind,
                bid,
                ask,
                bulletin_type,
                provider_metadata_json
            FROM fx_snapshot
            WHERE
        """
        sql += " AND ".join(where_clauses)
        sql += (
            " ORDER BY base_currency, quote_currency, snapshot_date DESC, "
            "observed_at DESC, provider_name"
        )

        rows = self.connection.execute(sql, parameters).fetchall()
        payload: dict[tuple[str, str], dict[str, object]] = {}
        for row in rows:
            item = _deserialize_fx_snapshot_row(row)
            pair = (str(item["base_currency"]), str(item["quote_currency"]))
            payload.setdefault(pair, item)
        return payload

    def count_rows(self, table_name: str, *, batch_id: str | None = None) -> int:
        if batch_id is None:
            row = self.connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        else:
            row = self.connection.execute(
                f"SELECT COUNT(*) AS count FROM {table_name} WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()
        return int(row["count"])

    def _fetch_group_counts(
        self,
        *,
        table_name: str,
        code_column: str,
        batch_id: str | None,
    ) -> dict[str, int]:
        if batch_id is None:
            rows = self.connection.execute(
                f"""
                SELECT {code_column} AS code, COUNT(*) AS count
                FROM {table_name}
                GROUP BY {code_column}
                """
            ).fetchall()
        else:
            rows = self.connection.execute(
                f"""
                SELECT {code_column} AS code, COUNT(*) AS count
                FROM {table_name}
                WHERE batch_id = ?
                GROUP BY {code_column}
                """,
                (batch_id,),
            ).fetchall()
        return {str(row["code"]): int(row["count"]) for row in rows}

    def _insert_import_batch(self, batch: ImportBatch) -> bool:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO import_batch (
                batch_id,
                source_system,
                source_file,
                file_sha256,
                imported_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                batch.batch_id,
                batch.source_system.value,
                batch.source_file,
                batch.file_sha256,
                batch.imported_at.isoformat(),
            ),
        )
        return cursor.rowcount > 0

    def _insert_source_records(self, bundle: IngestionBundle) -> int:
        source_records = _collect_source_records(bundle)
        cursor = self.connection.executemany(
            """
            INSERT OR IGNORE INTO source_record (
                source_record_id,
                batch_id,
                source_system,
                source_file,
                sheet_name,
                row_number,
                source_row_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    _source_record_id(record),
                    record.batch_id,
                    record.source_system.value,
                    record.source_file,
                    record.sheet_name,
                    record.row_number,
                    record.source_row_ref,
                )
                for record in source_records
            ],
        )
        return cursor.rowcount

    def _insert_transactions(self, transactions: tuple[CanonicalTransaction, ...]) -> int:
        cursor = self.connection.executemany(
            """
            INSERT OR IGNORE INTO canonical_transaction (
                transaction_id,
                batch_id,
                source_record_id,
                trade_date,
                transaction_type,
                instrument_code,
                instrument_type,
                asset_category,
                broker_name,
                quantity,
                unit_price,
                gross_amount,
                fees,
                cash_effect,
                cost_basis_effect,
                currency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.transaction_id,
                    item.source_record.batch_id,
                    _source_record_id(item.source_record),
                    item.trade_date.isoformat(),
                    item.transaction_type.value,
                    item.instrument_code,
                    item.instrument_type.value,
                    item.asset_category,
                    item.broker_name,
                    _decimal_str(item.quantity),
                    _decimal_str(item.unit_price),
                    _decimal_str(item.gross_amount),
                    _decimal_str(item.fees),
                    _decimal_str(item.cash_effect),
                    _decimal_str(item.cost_basis_effect),
                    item.currency,
                )
                for item in transactions
            ],
        )
        return cursor.rowcount

    def _insert_dividend_receipts(
        self,
        receipts: tuple[CanonicalDividendReceipt, ...],
    ) -> int:
        cursor = self.connection.executemany(
            """
            INSERT OR IGNORE INTO canonical_dividend_receipt (
                receipt_id,
                batch_id,
                source_record_id,
                reference_date,
                received_date,
                instrument_code,
                instrument_type,
                asset_category,
                broker_name,
                dividend_type,
                payable_quantity,
                gross_amount,
                withholding_tax,
                net_amount,
                currency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.receipt_id,
                    item.source_record.batch_id,
                    _source_record_id(item.source_record),
                    _date_str(item.reference_date),
                    item.received_date.isoformat(),
                    item.instrument_code,
                    item.instrument_type.value,
                    item.asset_category,
                    item.broker_name,
                    item.dividend_type.value,
                    _decimal_str(item.payable_quantity),
                    _decimal_str(item.gross_amount),
                    _decimal_str(item.withholding_tax),
                    _decimal_str(item.net_amount),
                    item.currency,
                )
                for item in receipts
            ],
        )
        return cursor.rowcount

    def _insert_corporate_actions(
        self,
        actions: tuple[CanonicalCorporateAction, ...],
    ) -> int:
        cursor = self.connection.executemany(
            """
            INSERT OR IGNORE INTO canonical_corporate_action (
                corporate_action_id,
                batch_id,
                source_record_id,
                action_type,
                effective_date,
                source_instrument_code,
                target_instrument_code,
                quantity_from,
                quantity_to,
                cost_basis_transferred,
                cash_component,
                comments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    item.corporate_action_id,
                    item.source_record.batch_id,
                    _source_record_id(item.source_record),
                    item.action_type.value,
                    item.effective_date.isoformat(),
                    item.source_instrument_code,
                    item.target_instrument_code,
                    _decimal_str(item.quantity_from),
                    _decimal_str(item.quantity_to),
                    _decimal_str(item.cost_basis_transferred),
                    _decimal_str(item.cash_component),
                    item.comments,
                )
                for item in actions
            ],
        )
        return cursor.rowcount


def _collect_source_records(bundle: IngestionBundle) -> list[SourceRecord]:
    ordered_records: dict[str, SourceRecord] = {}
    for record in (
        [item.source_record for item in bundle.transactions]
        + [item.source_record for item in bundle.dividend_receipts]
        + [item.source_record for item in bundle.corporate_actions]
    ):
        ordered_records.setdefault(_source_record_id(record), record)
    return list(ordered_records.values())


def _source_record_id(record: SourceRecord) -> str:
    return f"{record.batch_id}:{record.sheet_name}:{record.row_number}"


def _date_str(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _datetime_str(value: datetime | str) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _decimal_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _deserialize_market_snapshot_row(row: sqlite3.Row) -> dict[str, object]:
    payload = dict(row)
    metadata_json = payload.pop("provider_metadata_json")
    payload["provider_metadata"] = (
        json.loads(metadata_json) if isinstance(metadata_json, str) and metadata_json else {}
    )
    return payload


def _deserialize_fx_snapshot_row(row: sqlite3.Row) -> dict[str, object]:
    payload = dict(row)
    metadata_json = payload.pop("provider_metadata_json")
    payload["provider_metadata"] = (
        json.loads(metadata_json) if isinstance(metadata_json, str) and metadata_json else {}
    )
    return payload
