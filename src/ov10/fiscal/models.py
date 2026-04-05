from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_serialize_value(item) for item in value]
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


@dataclass(frozen=True, slots=True)
class FiscalDependencyGap:
    code: str
    severity: str
    summary: str
    affected_outputs: tuple[str, ...]
    note: str


@dataclass(frozen=True, slots=True)
class FiscalSectionSupport:
    section_id: str
    worksheet_range: str
    field_order: tuple[str, ...]
    support_level: str
    candidate_count: int
    current_source: str
    note: str


@dataclass(frozen=True, slots=True)
class DarfMonthlyBasis:
    month_end: date
    stock_sale_volume: Decimal
    etf_sale_volume: Decimal
    option_sale_volume: Decimal | None
    total_sale_volume: Decimal
    stock_positive_gain: Decimal | None = None
    stock_negative_gain: Decimal | None = None
    exempt_stock_gain_under_20k: Decimal | None = None
    exempt_asset_gain: Decimal | None = None
    stock_taxable_gain: Decimal | None = None
    etf_taxable_gain: Decimal | None = None
    gold_taxable_gain: Decimal | None = None
    option_taxable_gain: Decimal | None = None
    future_dollar_taxable_gain: Decimal | None = None
    future_index_taxable_gain: Decimal | None = None
    future_other_taxable_gain: Decimal | None = None
    term_taxable_gain: Decimal | None = None
    day_trade_net_gain: Decimal | None = None
    day_trade_taxable_gain: Decimal | None = None
    day_trade_tax_due: Decimal | None = None
    day_trade_withholding_tax: Decimal | None = None
    day_trade_withholding_balance: Decimal | None = None


@dataclass(frozen=True, slots=True)
class DarfContractReport:
    start_year: int
    investor_slot_range: str
    worksheet_header_range: str
    field_order: tuple[str, ...]
    supported_fields: tuple[str, ...]
    unsupported_fields: tuple[str, ...]
    monthly_rows: tuple[DarfMonthlyBasis, ...]


@dataclass(frozen=True, slots=True)
class DirpfAssetEntry:
    base_year: int
    instrument_code: str
    tax_code: str | None
    location_code: str | None
    cnpj: str | None
    description: str
    previous_amount: Decimal | None
    current_amount: Decimal | None
    snapshot_date: date


@dataclass(frozen=True, slots=True)
class DirpfDebtEntry:
    base_year: int
    tax_code: str | None
    location_code: str | None
    cnpj: str | None
    description: str
    previous_amount: Decimal | None
    current_amount: Decimal | None


@dataclass(frozen=True, slots=True)
class DirpfTaxExemptIncomeEntry:
    base_year: int
    tax_code: str | None
    payer_cnpj: str | None
    payer_name: str | None
    description: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class DirpfExclusiveTaxIncomeEntry:
    base_year: int
    tax_code: str | None
    payer_cnpj: str | None
    payer_name: str | None
    description: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class DirpfCarneLeaoEntry:
    base_year: int
    month_end: date
    tax_code: str | None
    description: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class DirpfContractReport:
    base_year: int
    investor_slot_range: str
    asset_entries: tuple[DirpfAssetEntry, ...]
    debt_entries: tuple[DirpfDebtEntry, ...]
    tax_exempt_income_entries: tuple[DirpfTaxExemptIncomeEntry, ...]
    exclusive_tax_income_entries: tuple[DirpfExclusiveTaxIncomeEntry, ...]
    carne_leao_entries: tuple[DirpfCarneLeaoEntry, ...]
    section_support: tuple[FiscalSectionSupport, ...]


@dataclass(frozen=True, slots=True)
class FiscalContractReport:
    source_workbook: str
    batch_id: str
    transaction_count: int
    dividend_receipt_count: int
    corporate_action_count: int
    snapshot_count: int
    darf: DarfContractReport
    dirpf: DirpfContractReport
    gaps: tuple[FiscalDependencyGap, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return _serialize_value(payload)
