from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ov10.domain.enums import InstrumentType, TransactionType
from ov10.domain.models import AccountPositionSnapshot, CanonicalTransaction, PositionSnapshot

POSITION_ENGINE_VERSION = "average_cost_v1"


@dataclass
class _PositionState:
    instrument_type: InstrumentType
    currency: str
    quantity: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    @property
    def avg_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")
        return self.total_cost / self.quantity


def compute_positions(
    transactions: list[CanonicalTransaction] | tuple[CanonicalTransaction, ...],
    *,
    snapshot_date: date | None = None,
) -> list[PositionSnapshot]:
    if not transactions:
        return []

    ordered_transactions = sorted(
        transactions,
        key=lambda item: (
            item.trade_date,
            item.source_record.sheet_name,
            item.source_record.row_number,
        ),
    )
    effective_date = snapshot_date or max(item.trade_date for item in ordered_transactions)
    states: dict[str, _PositionState] = {}

    for transaction in ordered_transactions:
        state = states.setdefault(
            transaction.instrument_code,
            _PositionState(
                instrument_type=transaction.instrument_type,
                currency=transaction.currency,
            ),
        )
        _apply_transaction(state, transaction)

    snapshots: list[PositionSnapshot] = []
    for instrument_code, state in sorted(states.items()):
        if state.quantity <= 0:
            continue
        snapshots.append(
            PositionSnapshot(
                snapshot_date=effective_date,
                instrument_code=instrument_code,
                instrument_type=state.instrument_type,
                quantity=state.quantity,
                total_cost=state.total_cost,
                avg_cost=state.avg_cost,
                currency=state.currency,
                engine_version=POSITION_ENGINE_VERSION,
            )
        )

    return snapshots


def compute_account_positions(
    transactions: list[CanonicalTransaction] | tuple[CanonicalTransaction, ...],
    *,
    account_ids_by_broker: dict[str, str],
    snapshot_date: date | None = None,
) -> list[AccountPositionSnapshot]:
    if not transactions:
        return []

    ordered_transactions = sorted(
        transactions,
        key=lambda item: (
            item.trade_date,
            item.source_record.sheet_name,
            item.source_record.row_number,
        ),
    )
    effective_date = snapshot_date or max(item.trade_date for item in ordered_transactions)
    states: dict[tuple[str, str], _PositionState] = {}

    for transaction in ordered_transactions:
        account_id = account_ids_by_broker[transaction.broker_name]
        state = states.setdefault(
            (account_id, transaction.instrument_code),
            _PositionState(
                instrument_type=transaction.instrument_type,
                currency=transaction.currency,
            ),
        )
        _apply_transaction(state, transaction)

    snapshots: list[AccountPositionSnapshot] = []
    for (account_id, instrument_code), state in sorted(states.items()):
        if state.quantity <= 0:
            continue
        snapshots.append(
            AccountPositionSnapshot(
                snapshot_date=effective_date,
                account_id=account_id,
                instrument_code=instrument_code,
                instrument_type=state.instrument_type,
                quantity=state.quantity,
                total_cost=state.total_cost,
                avg_cost=state.avg_cost,
                currency=state.currency,
                engine_version=POSITION_ENGINE_VERSION,
            )
        )

    return snapshots


def _apply_transaction(state: _PositionState, transaction: CanonicalTransaction) -> None:
    if transaction.transaction_type == TransactionType.BUY:
        state.quantity += transaction.quantity
        state.total_cost += transaction.cost_basis_effect or Decimal("0")
        return

    if transaction.transaction_type == TransactionType.BONUS:
        state.quantity += transaction.quantity
        return

    if transaction.transaction_type == TransactionType.CONVERSION_IN:
        state.quantity += transaction.quantity
        state.total_cost += transaction.cost_basis_effect or Decimal("0")
        return

    if transaction.transaction_type == TransactionType.CONVERSION_OUT:
        if state.quantity < transaction.quantity:
            raise ValueError(
                f"Conversion out exceeds open quantity for {transaction.instrument_code}: "
                f"{transaction.quantity} > {state.quantity}"
            )
        state.quantity -= transaction.quantity
        state.total_cost += transaction.cost_basis_effect or Decimal("0")
        if state.quantity == 0:
            state.total_cost = Decimal("0")
        return

    if transaction.transaction_type == TransactionType.SELL:
        if state.quantity < transaction.quantity:
            raise ValueError(
                f"Sell exceeds open quantity for {transaction.instrument_code}: "
                f"{transaction.quantity} > {state.quantity}"
            )
        average_cost = state.avg_cost
        state.quantity -= transaction.quantity
        state.total_cost -= average_cost * transaction.quantity
        if state.quantity == 0:
            state.total_cost = Decimal("0")
        return

    raise ValueError(f"Unsupported transaction type: {transaction.transaction_type}")
