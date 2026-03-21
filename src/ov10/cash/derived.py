from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ov10.domain.enums import AccountType, CashMovementType, TransactionType
from ov10.domain.models import (
    AccountRegistryEntry,
    CanonicalCorporateAction,
    CanonicalTransaction,
    CashBalanceSnapshot,
    CashMovement,
    IngestionBundle,
)

SYSTEM_ACCOUNT_NAME = "UNASSIGNED_CORPORATE_ACTIONS"
SYSTEM_ACCOUNT_ID = "system:account:unassigned_corporate_actions"


@dataclass(frozen=True, slots=True)
class DerivedCashLedger:
    accounts: tuple[AccountRegistryEntry, ...]
    movements: tuple[CashMovement, ...]
    balance_snapshots: tuple[CashBalanceSnapshot, ...]
    corporate_action_resolutions: tuple[CorporateActionCashResolution, ...]


@dataclass(frozen=True, slots=True)
class CorporateActionCashResolution:
    corporate_action_id: str
    account_id: str
    account_name: str
    reason: str
    candidate_brokers: tuple[str, ...]


def build_cash_ledger(
    bundle: IngestionBundle,
    *,
    snapshot_date: date | None = None,
) -> DerivedCashLedger:
    accounts = _build_broker_accounts(bundle)
    account_ids_by_name = {item.account_name: item.account_id for item in accounts}
    corporate_action_resolutions = _resolve_corporate_action_cash_accounts(
        bundle,
        account_ids_by_name=account_ids_by_name,
    )
    if any(item.account_id == SYSTEM_ACCOUNT_ID for item in corporate_action_resolutions):
        accounts.append(
            AccountRegistryEntry(
                account_id=SYSTEM_ACCOUNT_ID,
                source_system=bundle.batch.source_system,
                account_type=AccountType.SYSTEM,
                account_name=SYSTEM_ACCOUNT_NAME,
                first_batch_id=bundle.batch.batch_id,
                last_batch_id=bundle.batch.batch_id,
                currency="BRL",
            )
        )
    movements = _build_movements(
        bundle,
        account_ids_by_name=account_ids_by_name,
        corporate_action_resolutions={
            item.corporate_action_id: item for item in corporate_action_resolutions
        },
    )
    balance_snapshots = _build_balance_snapshots(
        movements=movements,
        batch_id=bundle.batch.batch_id,
        snapshot_date=snapshot_date,
    )
    return DerivedCashLedger(
        accounts=tuple(accounts),
        movements=tuple(movements),
        balance_snapshots=tuple(balance_snapshots),
        corporate_action_resolutions=tuple(corporate_action_resolutions),
    )


def _build_broker_accounts(bundle: IngestionBundle) -> list[AccountRegistryEntry]:
    batch_id = bundle.batch.batch_id
    accounts: list[AccountRegistryEntry] = []
    seen_account_ids: set[str] = set()

    for account_name in sorted(
        {item.broker_name for item in bundle.transactions}
        | {item.broker_name for item in bundle.dividend_receipts}
    ):
        account_id = _broker_account_id(bundle.batch.source_system.value, account_name)
        if account_id in seen_account_ids:
            continue
        accounts.append(
            AccountRegistryEntry(
                account_id=account_id,
                source_system=bundle.batch.source_system,
                account_type=AccountType.BROKER,
                account_name=account_name,
                first_batch_id=batch_id,
                last_batch_id=batch_id,
                currency="BRL",
            )
        )
        seen_account_ids.add(account_id)

    return accounts


def _build_movements(
    bundle: IngestionBundle,
    *,
    account_ids_by_name: dict[str, str],
    corporate_action_resolutions: dict[str, CorporateActionCashResolution],
) -> list[CashMovement]:
    movements: list[CashMovement] = []

    for item in bundle.transactions:
        if item.cash_effect == Decimal("0"):
            continue
        movements.append(
            CashMovement(
                movement_id=f"{item.transaction_id}:cash",
                batch_id=bundle.batch.batch_id,
                account_id=account_ids_by_name[item.broker_name],
                movement_date=item.trade_date,
                movement_type=CashMovementType.TRADE_SETTLEMENT,
                amount=item.cash_effect,
                currency=item.currency,
                related_record_type="canonical_transaction",
                related_record_id=item.transaction_id,
                instrument_code=item.instrument_code,
                description=item.transaction_type.value,
            )
        )

    for item in bundle.dividend_receipts:
        if item.net_amount == Decimal("0"):
            continue
        movements.append(
            CashMovement(
                movement_id=f"{item.receipt_id}:cash",
                batch_id=bundle.batch.batch_id,
                account_id=account_ids_by_name[item.broker_name],
                movement_date=item.received_date,
                movement_type=CashMovementType.DIVIDEND_RECEIPT,
                amount=item.net_amount,
                currency=item.currency,
                related_record_type="canonical_dividend_receipt",
                related_record_id=item.receipt_id,
                instrument_code=item.instrument_code,
                description=item.dividend_type.value,
            )
        )

    for item in bundle.corporate_actions:
        if item.cash_component == Decimal("0"):
            continue
        resolution = corporate_action_resolutions[item.corporate_action_id]
        movements.append(
            CashMovement(
                movement_id=f"{item.corporate_action_id}:cash",
                batch_id=bundle.batch.batch_id,
                account_id=resolution.account_id,
                movement_date=item.effective_date,
                movement_type=CashMovementType.CORPORATE_ACTION_CASH,
                amount=item.cash_component,
                currency="BRL",
                related_record_type="canonical_corporate_action",
                related_record_id=item.corporate_action_id,
                instrument_code=item.target_instrument_code,
                description=item.action_type.value,
            )
        )

    return sorted(
        movements,
        key=lambda item: (
            item.movement_date,
            item.account_id,
            item.movement_id,
        ),
    )


def _resolve_corporate_action_cash_accounts(
    bundle: IngestionBundle,
    *,
    account_ids_by_name: dict[str, str],
) -> list[CorporateActionCashResolution]:
    resolutions: list[CorporateActionCashResolution] = []

    for action in bundle.corporate_actions:
        if action.cash_component == Decimal("0"):
            continue

        historical_candidates = _find_historical_holder_brokers(
            action,
            bundle.transactions,
        )
        same_day_candidates = _find_same_day_conversion_brokers(
            action,
            bundle.transactions,
        )
        if len(historical_candidates) > 1:
            resolutions.append(
                CorporateActionCashResolution(
                    corporate_action_id=action.corporate_action_id,
                    account_id=SYSTEM_ACCOUNT_ID,
                    account_name=SYSTEM_ACCOUNT_NAME,
                    reason="ambiguous_candidate_brokers",
                    candidate_brokers=tuple(historical_candidates),
                )
            )
            continue

        if len(same_day_candidates) > 1:
            resolutions.append(
                CorporateActionCashResolution(
                    corporate_action_id=action.corporate_action_id,
                    account_id=SYSTEM_ACCOUNT_ID,
                    account_name=SYSTEM_ACCOUNT_NAME,
                    reason="ambiguous_candidate_brokers",
                    candidate_brokers=tuple(same_day_candidates),
                )
            )
            continue

        if len(same_day_candidates) == 1:
            broker_name = same_day_candidates[0]
            if historical_candidates and historical_candidates[0] != broker_name:
                resolutions.append(
                    CorporateActionCashResolution(
                        corporate_action_id=action.corporate_action_id,
                        account_id=SYSTEM_ACCOUNT_ID,
                        account_name=SYSTEM_ACCOUNT_NAME,
                        reason="ambiguous_candidate_brokers",
                        candidate_brokers=tuple(sorted({*historical_candidates, broker_name})),
                    )
                )
                continue
            resolutions.append(
                CorporateActionCashResolution(
                    corporate_action_id=action.corporate_action_id,
                    account_id=account_ids_by_name[broker_name],
                    account_name=broker_name,
                    reason="conversion_broker_match",
                    candidate_brokers=tuple(same_day_candidates),
                )
            )
            continue

        if len(historical_candidates) == 1:
            broker_name = historical_candidates[0]
            resolutions.append(
                CorporateActionCashResolution(
                    corporate_action_id=action.corporate_action_id,
                    account_id=account_ids_by_name[broker_name],
                    account_name=broker_name,
                    reason="historical_holding_match",
                    candidate_brokers=tuple(historical_candidates),
                )
            )
            continue

        reason = "ambiguous_candidate_brokers" if historical_candidates else "no_candidate_broker"
        resolutions.append(
            CorporateActionCashResolution(
                corporate_action_id=action.corporate_action_id,
                account_id=SYSTEM_ACCOUNT_ID,
                account_name=SYSTEM_ACCOUNT_NAME,
                reason=reason,
                candidate_brokers=tuple(historical_candidates),
            )
        )

    return resolutions


def _find_same_day_conversion_brokers(
    action: CanonicalCorporateAction,
    transactions: tuple[CanonicalTransaction, ...],
) -> list[str]:
    brokers = {
        item.broker_name
        for item in transactions
        if item.trade_date == action.effective_date
        and (
            (
                item.instrument_code == action.source_instrument_code
                and item.transaction_type == TransactionType.CONVERSION_OUT
            )
            or (
                item.instrument_code == action.target_instrument_code
                and item.transaction_type == TransactionType.CONVERSION_IN
            )
        )
    }
    return sorted(brokers)


def _find_historical_holder_brokers(
    action: CanonicalCorporateAction,
    transactions: tuple[CanonicalTransaction, ...],
) -> list[str]:
    quantity_by_broker: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in transactions:
        if item.trade_date >= action.effective_date:
            continue
        if item.instrument_code != action.source_instrument_code:
            continue
        quantity_by_broker[item.broker_name] += _signed_quantity(item)
    return sorted(
        broker_name
        for broker_name, quantity in quantity_by_broker.items()
        if quantity > Decimal("0")
    )


def _signed_quantity(item: CanonicalTransaction) -> Decimal:
    if item.transaction_type in {
        TransactionType.BUY,
        TransactionType.BONUS,
        TransactionType.CONVERSION_IN,
    }:
        return item.quantity
    if item.transaction_type in {
        TransactionType.SELL,
        TransactionType.CONVERSION_OUT,
    }:
        return -item.quantity
    return Decimal("0")


def _build_balance_snapshots(
    *,
    movements: list[CashMovement],
    batch_id: str,
    snapshot_date: date | None,
) -> list[CashBalanceSnapshot]:
    if not movements:
        return []

    balance_by_account_currency: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for item in movements:
        balance_by_account_currency[(item.account_id, item.currency)] += item.amount

    effective_date = snapshot_date or max(item.movement_date for item in movements)
    return [
        CashBalanceSnapshot(
            batch_id=batch_id,
            snapshot_date=effective_date,
            account_id=account_id,
            currency=currency,
            balance=balance,
        )
        for (account_id, currency), balance in sorted(balance_by_account_currency.items())
    ]


def _broker_account_id(source_system: str, account_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", account_name).encode("ascii", "ignore").decode()
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    return f"{source_system}:account:{normalized}"
