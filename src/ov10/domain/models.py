from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from ov10.domain.enums import (
    AccountType,
    CashMovementType,
    CorporateActionType,
    DividendType,
    InstrumentType,
    SourceSystem,
    TransactionType,
)


def _require_non_empty(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} cannot be empty")
    return normalized


def _require_upper_code(value: str, field_name: str) -> str:
    return _require_non_empty(value, field_name).upper()


def _require_currency(value: str) -> str:
    normalized = _require_upper_code(value, "currency")
    if len(normalized) != 3:
        raise ValueError("currency must have length 3")
    return normalized


def _require_decimal_at_least(value: Decimal, minimum: Decimal, field_name: str) -> None:
    if value < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")


@dataclass(frozen=True, slots=True)
class ImportBatch:
    batch_id: str
    source_system: SourceSystem
    source_file: str
    file_sha256: str
    imported_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", _require_non_empty(self.batch_id, "batch_id"))
        object.__setattr__(self, "source_file", _require_non_empty(self.source_file, "source_file"))
        object.__setattr__(self, "file_sha256", _require_non_empty(self.file_sha256, "file_sha256"))


@dataclass(frozen=True, slots=True)
class SourceRecord:
    batch_id: str
    source_system: SourceSystem
    source_file: str
    sheet_name: str
    row_number: int
    source_row_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", _require_non_empty(self.batch_id, "batch_id"))
        object.__setattr__(self, "source_file", _require_non_empty(self.source_file, "source_file"))
        object.__setattr__(self, "sheet_name", _require_non_empty(self.sheet_name, "sheet_name"))
        object.__setattr__(
            self,
            "source_row_ref",
            _require_non_empty(self.source_row_ref, "source_row_ref"),
        )
        if self.row_number < 2:
            raise ValueError("row_number must be >= 2")


@dataclass(frozen=True, slots=True)
class CanonicalTransaction:
    transaction_id: str
    source_record: SourceRecord
    trade_date: date
    transaction_type: TransactionType
    instrument_code: str
    instrument_type: InstrumentType
    asset_category: str
    broker_name: str
    quantity: Decimal
    unit_price: Decimal
    gross_amount: Decimal
    fees: Decimal
    cash_effect: Decimal
    cost_basis_effect: Decimal | None = None
    currency: str = "BRL"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "transaction_id",
            _require_non_empty(self.transaction_id, "transaction_id"),
        )
        object.__setattr__(
            self,
            "instrument_code",
            _require_upper_code(self.instrument_code, "instrument_code"),
        )
        object.__setattr__(
            self,
            "asset_category",
            _require_non_empty(self.asset_category, "asset_category"),
        )
        object.__setattr__(self, "broker_name", _require_non_empty(self.broker_name, "broker_name"))
        object.__setattr__(self, "currency", _require_currency(self.currency))
        _require_decimal_at_least(self.quantity, Decimal("0.0000000001"), "quantity")
        _require_decimal_at_least(self.unit_price, Decimal("0"), "unit_price")
        _require_decimal_at_least(self.gross_amount, Decimal("0"), "gross_amount")
        _require_decimal_at_least(self.fees, Decimal("0"), "fees")


@dataclass(frozen=True, slots=True)
class CanonicalDividendReceipt:
    receipt_id: str
    source_record: SourceRecord
    reference_date: date | None
    received_date: date
    instrument_code: str
    instrument_type: InstrumentType
    asset_category: str
    broker_name: str
    dividend_type: DividendType
    payable_quantity: Decimal
    gross_amount: Decimal
    withholding_tax: Decimal
    net_amount: Decimal
    currency: str = "BRL"

    def __post_init__(self) -> None:
        object.__setattr__(self, "receipt_id", _require_non_empty(self.receipt_id, "receipt_id"))
        object.__setattr__(
            self,
            "instrument_code",
            _require_upper_code(self.instrument_code, "instrument_code"),
        )
        object.__setattr__(
            self,
            "asset_category",
            _require_non_empty(self.asset_category, "asset_category"),
        )
        object.__setattr__(self, "broker_name", _require_non_empty(self.broker_name, "broker_name"))
        object.__setattr__(self, "currency", _require_currency(self.currency))
        _require_decimal_at_least(self.payable_quantity, Decimal("0"), "payable_quantity")
        _require_decimal_at_least(self.gross_amount, Decimal("0"), "gross_amount")
        _require_decimal_at_least(self.withholding_tax, Decimal("0"), "withholding_tax")
        _require_decimal_at_least(self.net_amount, Decimal("0"), "net_amount")


@dataclass(frozen=True, slots=True)
class CanonicalCorporateAction:
    corporate_action_id: str
    source_record: SourceRecord
    action_type: CorporateActionType
    effective_date: date
    source_instrument_code: str
    target_instrument_code: str
    quantity_from: Decimal
    quantity_to: Decimal
    cost_basis_transferred: Decimal
    cash_component: Decimal
    comments: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "corporate_action_id",
            _require_non_empty(self.corporate_action_id, "corporate_action_id"),
        )
        object.__setattr__(
            self,
            "source_instrument_code",
            _require_upper_code(self.source_instrument_code, "source_instrument_code"),
        )
        object.__setattr__(
            self,
            "target_instrument_code",
            _require_upper_code(self.target_instrument_code, "target_instrument_code"),
        )
        _require_decimal_at_least(self.quantity_from, Decimal("0.0000000001"), "quantity_from")
        _require_decimal_at_least(self.quantity_to, Decimal("0.0000000001"), "quantity_to")
        _require_decimal_at_least(
            self.cost_basis_transferred,
            Decimal("0"),
            "cost_basis_transferred",
        )
        _require_decimal_at_least(self.cash_component, Decimal("0"), "cash_component")


@dataclass(frozen=True, slots=True)
class AccountRegistryEntry:
    account_id: str
    source_system: SourceSystem
    account_type: AccountType
    account_name: str
    first_batch_id: str
    last_batch_id: str
    currency: str = "BRL"

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(
            self,
            "account_name",
            _require_non_empty(self.account_name, "account_name"),
        )
        object.__setattr__(
            self,
            "first_batch_id",
            _require_non_empty(self.first_batch_id, "first_batch_id"),
        )
        object.__setattr__(
            self,
            "last_batch_id",
            _require_non_empty(self.last_batch_id, "last_batch_id"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))


@dataclass(frozen=True, slots=True)
class CashMovement:
    movement_id: str
    batch_id: str
    account_id: str
    movement_date: date
    movement_type: CashMovementType
    amount: Decimal
    currency: str
    related_record_type: str
    related_record_id: str
    instrument_code: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "movement_id", _require_non_empty(self.movement_id, "movement_id"))
        object.__setattr__(self, "batch_id", _require_non_empty(self.batch_id, "batch_id"))
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(
            self,
            "related_record_type",
            _require_non_empty(self.related_record_type, "related_record_type"),
        )
        object.__setattr__(
            self,
            "related_record_id",
            _require_non_empty(self.related_record_id, "related_record_id"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))
        if self.instrument_code is not None:
            object.__setattr__(
                self,
                "instrument_code",
                _require_upper_code(self.instrument_code, "instrument_code"),
            )
        if self.amount == Decimal("0"):
            raise ValueError("amount must be non-zero")


@dataclass(frozen=True, slots=True)
class CashBalanceSnapshot:
    batch_id: str
    snapshot_date: date
    account_id: str
    currency: str
    balance: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", _require_non_empty(self.batch_id, "batch_id"))
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(self, "currency", _require_currency(self.currency))


@dataclass(frozen=True, slots=True)
class PortfolioDefinition:
    portfolio_id: str
    name: str
    short_name: str
    profile: str
    is_active: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty(self.portfolio_id, "portfolio_id"),
        )
        object.__setattr__(self, "name", _require_non_empty(self.name, "name"))
        object.__setattr__(self, "short_name", _require_non_empty(self.short_name, "short_name"))
        object.__setattr__(self, "profile", _require_non_empty(self.profile, "profile"))


@dataclass(frozen=True, slots=True)
class BookDefinition:
    book_id: str
    portfolio_id: str
    name: str
    target_weight: Decimal
    instrument_types: tuple[InstrumentType, ...]
    is_active: bool
    sort_order: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "book_id", _require_non_empty(self.book_id, "book_id"))
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty(self.portfolio_id, "portfolio_id"),
        )
        object.__setattr__(self, "name", _require_non_empty(self.name, "name"))
        _require_decimal_at_least(self.target_weight, Decimal("0"), "target_weight")
        if not self.instrument_types:
            raise ValueError("instrument_types cannot be empty")
        if self.sort_order < 0:
            raise ValueError("sort_order must be >= 0")


@dataclass(frozen=True, slots=True)
class AccountPortfolioAssignment:
    batch_id: str
    account_id: str
    portfolio_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "batch_id", _require_non_empty(self.batch_id, "batch_id"))
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty(self.portfolio_id, "portfolio_id"),
        )


@dataclass(frozen=True, slots=True)
class AccountPositionSnapshot:
    snapshot_date: date
    account_id: str
    instrument_code: str
    instrument_type: InstrumentType
    quantity: Decimal
    total_cost: Decimal
    avg_cost: Decimal
    currency: str
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(
            self,
            "instrument_code",
            _require_upper_code(self.instrument_code, "instrument_code"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))
        object.__setattr__(
            self,
            "engine_version",
            _require_non_empty(self.engine_version, "engine_version"),
        )
        _require_decimal_at_least(self.quantity, Decimal("0.0000000001"), "quantity")
        _require_decimal_at_least(self.total_cost, Decimal("0"), "total_cost")
        _require_decimal_at_least(self.avg_cost, Decimal("0"), "avg_cost")


@dataclass(frozen=True, slots=True)
class BookPositionSnapshot:
    snapshot_date: date
    portfolio_id: str
    book_id: str
    account_id: str
    instrument_code: str
    instrument_type: InstrumentType
    quantity: Decimal
    total_cost: Decimal
    avg_cost: Decimal
    currency: str
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "portfolio_id",
            _require_non_empty(self.portfolio_id, "portfolio_id"),
        )
        object.__setattr__(self, "book_id", _require_non_empty(self.book_id, "book_id"))
        object.__setattr__(self, "account_id", _require_non_empty(self.account_id, "account_id"))
        object.__setattr__(
            self,
            "instrument_code",
            _require_upper_code(self.instrument_code, "instrument_code"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))
        object.__setattr__(
            self,
            "engine_version",
            _require_non_empty(self.engine_version, "engine_version"),
        )
        _require_decimal_at_least(self.quantity, Decimal("0.0000000001"), "quantity")
        _require_decimal_at_least(self.total_cost, Decimal("0"), "total_cost")
        _require_decimal_at_least(self.avg_cost, Decimal("0"), "avg_cost")


@dataclass(frozen=True, slots=True)
class PositionSnapshot:
    snapshot_date: date
    instrument_code: str
    instrument_type: InstrumentType
    quantity: Decimal
    total_cost: Decimal
    avg_cost: Decimal
    currency: str
    engine_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "instrument_code",
            _require_upper_code(self.instrument_code, "instrument_code"),
        )
        object.__setattr__(self, "currency", _require_currency(self.currency))
        object.__setattr__(
            self,
            "engine_version",
            _require_non_empty(self.engine_version, "engine_version"),
        )
        _require_decimal_at_least(self.quantity, Decimal("0.0000000001"), "quantity")
        _require_decimal_at_least(self.total_cost, Decimal("0"), "total_cost")
        _require_decimal_at_least(self.avg_cost, Decimal("0"), "avg_cost")


@dataclass(frozen=True, slots=True)
class IngestionBundle:
    batch: ImportBatch
    transactions: tuple[CanonicalTransaction, ...]
    dividend_receipts: tuple[CanonicalDividendReceipt, ...]
    corporate_actions: tuple[CanonicalCorporateAction, ...]

    def summary(self) -> dict[str, object]:
        transaction_types = Counter(item.transaction_type for item in self.transactions)
        dividend_types = Counter(item.dividend_type for item in self.dividend_receipts)
        return {
            "batch_id": self.batch.batch_id,
            "source_system": self.batch.source_system.value,
            "source_file": self.batch.source_file,
            "transactions": len(self.transactions),
            "dividend_receipts": len(self.dividend_receipts),
            "corporate_actions": len(self.corporate_actions),
            "transaction_types": {key.value: value for key, value in transaction_types.items()},
            "dividend_types": {key.value: value for key, value in dividend_types.items()},
        }
