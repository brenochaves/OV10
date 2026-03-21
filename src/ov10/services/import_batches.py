from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from ov10.allocation import assign_account_positions_to_books, assign_accounts_to_portfolios
from ov10.cash import SYSTEM_ACCOUNT_ID, DerivedCashLedger, build_cash_ledger
from ov10.config import load_portfolio_book_config
from ov10.domain.enums import CorporateActionType, InstrumentType, TransactionType
from ov10.domain.models import (
    CanonicalTransaction,
    IngestionBundle,
    PositionSnapshot,
)
from ov10.ingestion import load_status_invest_workbook
from ov10.positions import POSITION_ENGINE_VERSION, compute_account_positions, compute_positions
from ov10.reference import build_instrument_references
from ov10.storage import SQLiteOV10Store, initialize_database

DEFAULT_PORTFOLIO_CONFIG_PATH = Path("config/ov10_portfolio.toml")


@dataclass(frozen=True, slots=True)
class ReconciliationIssue:
    code: str
    severity: str
    message: str
    context: dict[str, object]


@dataclass(frozen=True, slots=True)
class BatchReconciliationReport:
    batch_id: str
    engine_version: str
    transaction_count: int
    dividend_receipt_count: int
    corporate_action_count: int
    source_record_count: int
    mapping_count: int
    snapshot_count: int
    issue_count: int
    has_errors: bool
    issues: tuple[ReconciliationIssue, ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BatchPersistenceReport:
    database_path: str
    config_path: str
    batch_id: str
    engine_version: str
    batch_created: bool
    portfolios_loaded: int
    books_loaded: int
    accounts_observed: int
    account_assignments_persisted: int
    source_records_inserted: int
    transactions_inserted: int
    dividend_receipts_inserted: int
    corporate_actions_inserted: int
    mappings_observed: int
    instrument_references_persisted: int
    cash_movements_persisted: int
    cash_balance_snapshots_persisted: int
    account_position_snapshots_persisted: int
    book_position_snapshots_persisted: int
    snapshots_persisted: int
    reconciliation: BatchReconciliationReport

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["reconciliation"]["created_at"] = self.reconciliation.created_at.isoformat()
        return payload


def persist_status_invest_xlsx(
    workbook_path: str | Path,
    *,
    database_path: str | Path,
    config_path: str | Path = DEFAULT_PORTFOLIO_CONFIG_PATH,
    snapshot_date: date | None = None,
) -> BatchPersistenceReport:
    bundle = load_status_invest_workbook(workbook_path)
    snapshots = compute_positions(bundle.transactions, snapshot_date=snapshot_date)
    mappings = _build_observed_mappings(bundle)
    instrument_references = build_instrument_references(bundle)
    cash_ledger = build_cash_ledger(bundle, snapshot_date=snapshot_date)
    config_path = Path(config_path)
    fallback_config_path = (
        DEFAULT_PORTFOLIO_CONFIG_PATH if config_path.suffix.lower() in {".xlsx", ".xlsm"} else None
    )
    portfolio_config = load_portfolio_book_config(
        config_path,
        fallback_path=fallback_config_path,
    )
    account_ids_by_broker = {item.account_name: item.account_id for item in cash_ledger.accounts}
    account_positions = compute_account_positions(
        bundle.transactions,
        account_ids_by_broker=account_ids_by_broker,
        snapshot_date=snapshot_date,
    )
    account_assignments = assign_accounts_to_portfolios(
        cash_ledger.accounts,
        portfolio_config,
        batch_id=bundle.batch.batch_id,
    )
    book_positions = assign_account_positions_to_books(
        account_positions,
        account_assignments,
        portfolio_config,
    )
    reconciliation = _build_reconciliation_report(
        bundle=bundle,
        cash_ledger=cash_ledger,
        snapshots=snapshots,
        mapping_count=len(mappings),
    )

    initialize_database(database_path)
    with SQLiteOV10Store(database_path) as store:
        persisted_counts = store.persist_ingestion_bundle(bundle)
        portfolios_loaded = store.upsert_portfolios(list(portfolio_config.portfolios))
        books_loaded = store.upsert_books(list(portfolio_config.books))
        accounts_observed = store.upsert_accounts(list(cash_ledger.accounts))
        account_assignments_persisted = store.replace_account_portfolio_assignments(
            batch_id=bundle.batch.batch_id,
            assignments=account_assignments,
        )
        mappings_observed = store.upsert_instrument_mappings(
            batch_id=bundle.batch.batch_id,
            mappings=mappings,
        )
        instrument_references_persisted = store.upsert_instrument_references(instrument_references)
        cash_movements_persisted = store.replace_cash_movements(
            batch_id=bundle.batch.batch_id,
            movements=list(cash_ledger.movements),
        )
        cash_balance_snapshots_persisted = store.replace_cash_balance_snapshots(
            batch_id=bundle.batch.batch_id,
            snapshots=list(cash_ledger.balance_snapshots),
        )
        account_position_snapshots_persisted = store.replace_account_position_snapshots(
            batch_id=bundle.batch.batch_id,
            engine_version=POSITION_ENGINE_VERSION,
            snapshots=account_positions,
        )
        book_position_snapshots_persisted = store.replace_book_position_snapshots(
            batch_id=bundle.batch.batch_id,
            engine_version=POSITION_ENGINE_VERSION,
            snapshots=book_positions,
        )
        snapshots_persisted = store.replace_position_snapshots(
            batch_id=bundle.batch.batch_id,
            engine_version=POSITION_ENGINE_VERSION,
            snapshots=snapshots,
        )
        store.replace_batch_reconciliation(
            batch_id=bundle.batch.batch_id,
            engine_version=POSITION_ENGINE_VERSION,
            report={
                "transaction_count": reconciliation.transaction_count,
                "dividend_receipt_count": reconciliation.dividend_receipt_count,
                "corporate_action_count": reconciliation.corporate_action_count,
                "source_record_count": reconciliation.source_record_count,
                "mapping_count": reconciliation.mapping_count,
                "snapshot_count": reconciliation.snapshot_count,
                "issue_count": reconciliation.issue_count,
                "has_errors": reconciliation.has_errors,
                "issues": [asdict(item) for item in reconciliation.issues],
                "created_at": reconciliation.created_at,
            },
        )

    return BatchPersistenceReport(
        database_path=str(Path(database_path).resolve()),
        config_path=str(Path(config_path).resolve()),
        batch_id=bundle.batch.batch_id,
        engine_version=POSITION_ENGINE_VERSION,
        batch_created=bool(persisted_counts["batch_created"]),
        portfolios_loaded=portfolios_loaded,
        books_loaded=books_loaded,
        accounts_observed=accounts_observed,
        account_assignments_persisted=account_assignments_persisted,
        source_records_inserted=int(persisted_counts["source_records_inserted"]),
        transactions_inserted=int(persisted_counts["transactions_inserted"]),
        dividend_receipts_inserted=int(persisted_counts["dividend_receipts_inserted"]),
        corporate_actions_inserted=int(persisted_counts["corporate_actions_inserted"]),
        mappings_observed=mappings_observed,
        instrument_references_persisted=instrument_references_persisted,
        cash_movements_persisted=cash_movements_persisted,
        cash_balance_snapshots_persisted=cash_balance_snapshots_persisted,
        account_position_snapshots_persisted=account_position_snapshots_persisted,
        book_position_snapshots_persisted=book_position_snapshots_persisted,
        snapshots_persisted=snapshots_persisted,
        reconciliation=reconciliation,
    )


def _build_reconciliation_report(
    *,
    bundle: IngestionBundle,
    cash_ledger: DerivedCashLedger,
    snapshots: list[PositionSnapshot],
    mapping_count: int,
) -> BatchReconciliationReport:
    issues = [
        *_find_duplicate_id_issues(
            [item.transaction_id for item in bundle.transactions],
            record_kind="transaction",
        ),
        *_find_duplicate_id_issues(
            [item.receipt_id for item in bundle.dividend_receipts],
            record_kind="dividend_receipt",
        ),
        *_find_duplicate_id_issues(
            [item.corporate_action_id for item in bundle.corporate_actions],
            record_kind="corporate_action",
        ),
        *_find_duplicate_source_record_issues(bundle),
        *_find_unknown_type_issues(bundle),
        *_find_missing_cost_basis_issues(bundle.transactions),
        *_find_conversion_alignment_issues(bundle),
        *_find_system_cash_account_issues(cash_ledger),
    ]

    source_record_count = len(
        {
            (
                item.source_record.batch_id,
                item.source_record.sheet_name,
                item.source_record.row_number,
            )
            for item in bundle.transactions
        }
        | {
            (
                item.source_record.batch_id,
                item.source_record.sheet_name,
                item.source_record.row_number,
            )
            for item in bundle.dividend_receipts
        }
        | {
            (
                item.source_record.batch_id,
                item.source_record.sheet_name,
                item.source_record.row_number,
            )
            for item in bundle.corporate_actions
        }
    )

    return BatchReconciliationReport(
        batch_id=bundle.batch.batch_id,
        engine_version=POSITION_ENGINE_VERSION,
        transaction_count=len(bundle.transactions),
        dividend_receipt_count=len(bundle.dividend_receipts),
        corporate_action_count=len(bundle.corporate_actions),
        source_record_count=source_record_count,
        mapping_count=mapping_count,
        snapshot_count=len(snapshots),
        issue_count=len(issues),
        has_errors=any(item.severity == "error" for item in issues),
        issues=tuple(issues),
        created_at=datetime.now(UTC),
    )


def _find_duplicate_id_issues(ids: list[str], *, record_kind: str) -> list[ReconciliationIssue]:
    duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
    if not duplicates:
        return []
    return [
        ReconciliationIssue(
            code=f"duplicate_{record_kind}_ids",
            severity="error",
            message=f"Found duplicate {record_kind} identifiers.",
            context={"duplicates": duplicates[:10], "total_duplicates": len(duplicates)},
        )
    ]


def _find_duplicate_source_record_issues(bundle: IngestionBundle) -> list[ReconciliationIssue]:
    references = [
        item.source_record.source_row_ref
        for item in bundle.transactions + bundle.dividend_receipts + bundle.corporate_actions
    ]
    duplicates = sorted(item for item, count in Counter(references).items() if count > 1)
    if not duplicates:
        return []
    return [
        ReconciliationIssue(
            code="duplicate_source_row_refs",
            severity="error",
            message="Found duplicate source row references across canonical records.",
            context={"duplicates": duplicates[:10], "total_duplicates": len(duplicates)},
        )
    ]


def _find_unknown_type_issues(bundle: IngestionBundle) -> list[ReconciliationIssue]:
    issues: list[ReconciliationIssue] = []

    unknown_instruments = sorted(
        {
            item.instrument_code
            for item in bundle.transactions
            if item.instrument_type == InstrumentType.UNKNOWN
        }
        | {
            item.instrument_code
            for item in bundle.dividend_receipts
            if item.instrument_type == InstrumentType.UNKNOWN
        }
    )
    if unknown_instruments:
        issues.append(
            ReconciliationIssue(
                code="unknown_instrument_types",
                severity="warning",
                message="Some instrument categories are not mapped yet.",
                context={
                    "instrument_codes": unknown_instruments[:20],
                    "total_unknown_instruments": len(unknown_instruments),
                },
            )
        )

    unknown_actions = [
        item.corporate_action_id
        for item in bundle.corporate_actions
        if item.action_type == CorporateActionType.UNKNOWN
    ]
    if unknown_actions:
        issues.append(
            ReconciliationIssue(
                code="unknown_corporate_action_types",
                severity="warning",
                message="Some corporate actions could not be classified.",
                context={
                    "corporate_action_ids": unknown_actions[:20],
                    "total": len(unknown_actions),
                },
            )
        )

    return issues


def _find_missing_cost_basis_issues(
    transactions: tuple[CanonicalTransaction, ...],
) -> list[ReconciliationIssue]:
    missing = [
        item.transaction_id
        for item in transactions
        if item.transaction_type
        in {
            TransactionType.BUY,
            TransactionType.BONUS,
            TransactionType.CONVERSION_IN,
            TransactionType.CONVERSION_OUT,
        }
        and item.cost_basis_effect is None
    ]
    if not missing:
        return []
    return [
        ReconciliationIssue(
            code="missing_cost_basis_effect",
            severity="error",
            message="Some inventory-affecting transactions are missing cost basis effect.",
            context={"transaction_ids": missing[:20], "total": len(missing)},
        )
    ]


def _find_conversion_alignment_issues(bundle: IngestionBundle) -> list[ReconciliationIssue]:
    issues: list[ReconciliationIssue] = []
    outgoing_quantities: dict[tuple[date, str], Decimal] = defaultdict(lambda: Decimal("0"))
    incoming_quantities: dict[tuple[date, str], Decimal] = defaultdict(lambda: Decimal("0"))

    for item in bundle.transactions:
        key = (item.trade_date, item.instrument_code)
        if item.transaction_type == TransactionType.CONVERSION_OUT:
            outgoing_quantities[key] += item.quantity
        elif item.transaction_type == TransactionType.CONVERSION_IN:
            incoming_quantities[key] += item.quantity

    for action in bundle.corporate_actions:
        outgoing = outgoing_quantities[(action.effective_date, action.source_instrument_code)]
        incoming = incoming_quantities[(action.effective_date, action.target_instrument_code)]
        if outgoing != action.quantity_from or incoming != action.quantity_to:
            issues.append(
                ReconciliationIssue(
                    code="conversion_alignment_mismatch",
                    severity="warning",
                    message="Corporate action quantities do not match the conversion transactions.",
                    context={
                        "corporate_action_id": action.corporate_action_id,
                        "source_instrument_code": action.source_instrument_code,
                        "target_instrument_code": action.target_instrument_code,
                        "expected_quantity_from": str(action.quantity_from),
                        "observed_quantity_from": str(outgoing),
                        "expected_quantity_to": str(action.quantity_to),
                        "observed_quantity_to": str(incoming),
                    },
                )
            )

    return issues


def _find_system_cash_account_issues(cash_ledger: DerivedCashLedger) -> list[ReconciliationIssue]:
    unresolved_resolutions = [
        item
        for item in cash_ledger.corporate_action_resolutions
        if item.account_id == SYSTEM_ACCOUNT_ID
    ]
    if not unresolved_resolutions:
        return []

    unresolved_ids = {item.corporate_action_id for item in unresolved_resolutions}
    system_movements = [
        item
        for item in cash_ledger.movements
        if item.account_id == SYSTEM_ACCOUNT_ID and item.related_record_id in unresolved_ids
    ]
    amount_by_action_id = {item.related_record_id: item.amount for item in system_movements}
    reason_config = {
        "no_candidate_broker": (
            "system_cash_account_used_no_candidate",
            "Corporate action cash could not be tied to any broker candidate.",
        ),
        "ambiguous_candidate_brokers": (
            "system_cash_account_used_ambiguous",
            "Corporate action cash matched multiple broker candidates and remained unresolved.",
        ),
    }

    issues: list[ReconciliationIssue] = []
    for reason, (code, message) in reason_config.items():
        matching = [item for item in unresolved_resolutions if item.reason == reason]
        if not matching:
            continue
        total_amount = sum(
            (amount_by_action_id.get(item.corporate_action_id, Decimal("0")) for item in matching),
            Decimal("0"),
        )
        issues.append(
            ReconciliationIssue(
                code=code,
                severity="warning",
                message=message,
                context={
                    "account_id": SYSTEM_ACCOUNT_ID,
                    "corporate_action_ids": [item.corporate_action_id for item in matching],
                    "candidate_brokers_by_action": {
                        item.corporate_action_id: list(item.candidate_brokers) for item in matching
                    },
                    "movement_count": len(matching),
                    "total_amount": str(total_amount),
                },
            )
        )

    return issues


def _build_observed_mappings(bundle: IngestionBundle) -> list[dict[str, str]]:
    observed: dict[tuple[str, str], dict[str, str]] = {}

    for item in bundle.transactions:
        _remember_mapping(
            observed=observed,
            source_system=bundle.batch.source_system.value,
            source_code=item.instrument_code,
            canonical_code=item.instrument_code,
            instrument_type=item.instrument_type.value,
            first_batch_id=bundle.batch.batch_id,
        )

    for item in bundle.dividend_receipts:
        _remember_mapping(
            observed=observed,
            source_system=bundle.batch.source_system.value,
            source_code=item.instrument_code,
            canonical_code=item.instrument_code,
            instrument_type=item.instrument_type.value,
            first_batch_id=bundle.batch.batch_id,
        )

    for item in bundle.corporate_actions:
        _remember_mapping(
            observed=observed,
            source_system=bundle.batch.source_system.value,
            source_code=item.source_instrument_code,
            canonical_code=item.source_instrument_code,
            instrument_type=InstrumentType.UNKNOWN.value,
            first_batch_id=bundle.batch.batch_id,
        )
        _remember_mapping(
            observed=observed,
            source_system=bundle.batch.source_system.value,
            source_code=item.target_instrument_code,
            canonical_code=item.target_instrument_code,
            instrument_type=InstrumentType.UNKNOWN.value,
            first_batch_id=bundle.batch.batch_id,
        )

    return sorted(observed.values(), key=lambda item: item["source_code"])


def _remember_mapping(
    *,
    observed: dict[tuple[str, str], dict[str, str]],
    source_system: str,
    source_code: str,
    canonical_code: str,
    instrument_type: str,
    first_batch_id: str,
) -> None:
    key = (source_system, source_code)
    current = observed.get(key)
    if current is None:
        observed[key] = {
            "mapping_id": f"{source_system}:{source_code}",
            "source_system": source_system,
            "source_code": source_code,
            "canonical_code": canonical_code,
            "instrument_type": instrument_type,
            "mapping_origin": "observed_identity",
            "first_batch_id": first_batch_id,
            "notes": "Auto-created from observed source instrument code.",
        }
        return

    if (
        current["instrument_type"] == InstrumentType.UNKNOWN.value
        and instrument_type != current["instrument_type"]
    ):
        current["instrument_type"] = instrument_type
