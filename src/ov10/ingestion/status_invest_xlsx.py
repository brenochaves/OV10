from __future__ import annotations

import hashlib
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pandas as pd

from ov10.domain.enums import (
    CorporateActionType,
    DividendType,
    InstrumentType,
    SourceSystem,
    TransactionType,
)
from ov10.domain.models import (
    CanonicalCorporateAction,
    CanonicalDividendReceipt,
    CanonicalTransaction,
    ImportBatch,
    IngestionBundle,
    SourceRecord,
)

SHEET_ALIASES = {
    "transactions": ("OperaÃ§Ãµes", "Operações", "Operacoes", "OperaĂ§Ăľes"),
    "dividends": ("Proventos",),
    "corporate_actions": ("Conversoes_Mapeadas", "Conversões_Mapeadas"),
}

TRANSACTION_COLUMN_ALIASES = {
    "order": ("ORDEM",),
    "quantity": ("QUANTIDADE",),
    "unit_price": ("PREÃ‡O", "PREÇO", "PRECO"),
    "line_total": ("TOTAL",),
    "trade_date": ("NEGOCIAÃ‡ÃƒO", "NEGOCIAÇÃO", "NEGOCIACAO"),
    "instrument_code": ("Ativo", "ATIVO"),
    "category": ("CATEGORIA",),
    "broker_name": ("BROKER",),
}

DIVIDEND_COLUMN_ALIASES = {
    "gross_amount": ("Total", "TOTAL"),
    "net_amount": ("Total lÃ­q.", "Total líq.", "Total_liq"),
    "reference_date": ("Data com", "Data_com"),
    "payment_date": ("Pagamento", "PAGAMENTO"),
    "instrument_code": ("Ativo", "ATIVO"),
    "category": ("CATEGORIA",),
    "broker_name": ("Corretora/banco", "Corretora_banco"),
    "dividend_type": ("Tipo", "TIPO"),
    "quantity": ("Quantidade", "QUANTIDADE"),
}

CORPORATE_ACTION_COLUMN_ALIASES = {
    "cash_component": ("Valor_Retornado",),
    "average_price": ("Preco_Medio", "Preço_Medio"),
    "quantity_from": ("Quantidade_De",),
    "action_type": ("Tipo_Conversao", "Tipo_Conversão"),
    "effective_date": ("Data_Conversao", "Data_Conversão"),
    "source_instrument_code": ("Ativo_De",),
    "target_instrument_code": ("Ativo_Para",),
    "quantity_to": ("Quantidade_Para",),
    "observations": ("Observacoes", "Observações"),
}

TRANSACTION_TYPE_MAP = {
    "Compra": TransactionType.BUY,
    "Venda": TransactionType.SELL,
    "BonificaÃ§Ã£o": TransactionType.BONUS,
    "Bonificação": TransactionType.BONUS,
    "ConversÃ£o (E)": TransactionType.CONVERSION_IN,
    "Conversão (E)": TransactionType.CONVERSION_IN,
    "ConversÃ£o (S)": TransactionType.CONVERSION_OUT,
    "Conversão (S)": TransactionType.CONVERSION_OUT,
}

DIVIDEND_TYPE_MAP = {
    "Dividendo": DividendType.DIVIDEND,
    "JCP": DividendType.JCP,
    "Rendimento": DividendType.INCOME,
    "Rend. Tributado": DividendType.TAXABLE_INCOME,
}

CORPORATE_ACTION_TYPE_MAP = {
    "IncorporaÃ§Ã£o Total": CorporateActionType.INCORPORATION_TOTAL,
    "Incorporação Total": CorporateActionType.INCORPORATION_TOTAL,
    "ConversÃ£o Simples": CorporateActionType.SIMPLE_CONVERSION,
    "Conversão Simples": CorporateActionType.SIMPLE_CONVERSION,
}

INSTRUMENT_TYPE_MAP = {
    "AÃ§Ãµes": InstrumentType.STOCK_BR,
    "Ações": InstrumentType.STOCK_BR,
    "FIIs": InstrumentType.FII,
    "BDR": InstrumentType.BDR,
    "ETF": InstrumentType.ETF_BR,
    "ETF Exterior": InstrumentType.ETF_US,
    "Stocks": InstrumentType.STOCK_US,
    "Fundos Invest.": InstrumentType.FUND_BR,
    "Tesouro": InstrumentType.TREASURY_BR,
    "Criptomoedas": InstrumentType.CRYPTO,
}


def load_status_invest_workbook(path: str | Path) -> IngestionBundle:
    workbook_path = Path(path)
    if not workbook_path.exists():
        raise FileNotFoundError(workbook_path)

    batch = _build_batch(workbook_path)
    with pd.ExcelFile(workbook_path) as workbook:
        sheet_names = _resolve_sheet_names(tuple(workbook.sheet_names))
        transactions = _parse_transactions(
            workbook,
            workbook_path,
            batch,
            sheet_name=sheet_names["transactions"],
        )
        dividend_receipts = _parse_dividend_receipts(
            workbook,
            workbook_path,
            batch,
            sheet_name=sheet_names["dividends"],
        )
        corporate_actions = _parse_corporate_actions(
            workbook,
            workbook_path,
            batch,
            sheet_name=sheet_names["corporate_actions"],
        )

    return IngestionBundle(
        batch=batch,
        transactions=tuple(transactions),
        dividend_receipts=tuple(dividend_receipts),
        corporate_actions=tuple(corporate_actions),
    )


def _build_batch(path: Path) -> ImportBatch:
    file_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return ImportBatch(
        batch_id=f"{SourceSystem.STATUS_INVEST_XLSX.value}:{file_sha256[:12]}",
        source_system=SourceSystem.STATUS_INVEST_XLSX,
        source_file=str(path.resolve()),
        file_sha256=file_sha256,
        imported_at=datetime.now(UTC),
    )


def _resolve_sheet_names(sheet_names: tuple[str, ...]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for canonical_name, aliases in SHEET_ALIASES.items():
        for alias in aliases:
            if alias in sheet_names:
                resolved[canonical_name] = alias
                break
        else:
            missing.append(aliases[0])
    if missing:
        raise ValueError(f"Missing expected sheet(s): {', '.join(missing)}")
    return resolved


def _parse_transactions(
    workbook: pd.ExcelFile,
    workbook_path: Path,
    batch: ImportBatch,
    *,
    sheet_name: str,
) -> list[CanonicalTransaction]:
    frame = _load_frame(workbook, sheet_name=sheet_name, aliases=TRANSACTION_COLUMN_ALIASES)
    records: list[CanonicalTransaction] = []

    for index, row in frame.iterrows():
        row_number = _coerce_row_index(index) + 2
        transaction_type = _map_transaction_type(row["order"])
        quantity = _to_decimal(row["quantity"])
        unit_price = _to_decimal(row["unit_price"])
        line_total = _to_decimal(row["line_total"])
        gross_amount = quantity * unit_price
        fees = _positive_decimal(line_total - gross_amount)
        source_record = _build_source_record(
            batch=batch,
            workbook_path=workbook_path,
            sheet_name=sheet_name,
            row_number=row_number,
        )
        records.append(
            CanonicalTransaction(
                transaction_id=f"{batch.batch_id}:txn:{row_number}",
                source_record=source_record,
                trade_date=_to_date(row["trade_date"]),
                transaction_type=transaction_type,
                instrument_code=str(row["instrument_code"]),
                instrument_type=_map_instrument_type(row["category"]),
                asset_category=str(row["category"]),
                broker_name=str(row["broker_name"]),
                quantity=quantity,
                unit_price=unit_price,
                gross_amount=gross_amount,
                fees=fees,
                cash_effect=_compute_cash_effect(transaction_type, line_total),
                cost_basis_effect=_compute_cost_basis_effect(transaction_type, line_total),
                currency="BRL",
            )
        )

    return records


def _parse_dividend_receipts(
    workbook: pd.ExcelFile,
    workbook_path: Path,
    batch: ImportBatch,
    *,
    sheet_name: str,
) -> list[CanonicalDividendReceipt]:
    frame = _load_frame(workbook, sheet_name=sheet_name, aliases=DIVIDEND_COLUMN_ALIASES)
    records: list[CanonicalDividendReceipt] = []

    for index, row in frame.iterrows():
        row_number = _coerce_row_index(index) + 2
        gross_amount = _to_decimal(row["gross_amount"])
        net_amount = _to_decimal(row["net_amount"])
        withholding_tax = _positive_decimal(gross_amount - net_amount)
        source_record = _build_source_record(
            batch=batch,
            workbook_path=workbook_path,
            sheet_name=sheet_name,
            row_number=row_number,
        )
        records.append(
            CanonicalDividendReceipt(
                receipt_id=f"{batch.batch_id}:div:{row_number}",
                source_record=source_record,
                reference_date=_to_optional_date(row.get("reference_date")),
                received_date=_to_date(row["payment_date"]),
                instrument_code=str(row["instrument_code"]),
                instrument_type=_map_instrument_type(row["category"]),
                asset_category=str(row["category"]),
                broker_name=str(row["broker_name"]),
                dividend_type=_map_dividend_type(row["dividend_type"]),
                payable_quantity=_to_decimal(row["quantity"]),
                gross_amount=gross_amount,
                withholding_tax=withholding_tax,
                net_amount=net_amount,
                currency="BRL",
            )
        )

    return records


def _parse_corporate_actions(
    workbook: pd.ExcelFile,
    workbook_path: Path,
    batch: ImportBatch,
    *,
    sheet_name: str,
) -> list[CanonicalCorporateAction]:
    frame = _load_frame(
        workbook,
        sheet_name=sheet_name,
        aliases=CORPORATE_ACTION_COLUMN_ALIASES,
    )
    records: list[CanonicalCorporateAction] = []

    for index, row in frame.iterrows():
        row_number = _coerce_row_index(index) + 2
        source_record = _build_source_record(
            batch=batch,
            workbook_path=workbook_path,
            sheet_name=sheet_name,
            row_number=row_number,
        )
        cash_component = _to_decimal(row.get("cash_component"))
        average_price = _to_decimal(row["average_price"])
        quantity_from = _to_decimal(row["quantity_from"])
        records.append(
            CanonicalCorporateAction(
                corporate_action_id=f"{batch.batch_id}:ca:{row_number}",
                source_record=source_record,
                action_type=_map_corporate_action_type(row["action_type"]),
                effective_date=_to_date(row["effective_date"]),
                source_instrument_code=str(row["source_instrument_code"]),
                target_instrument_code=str(row["target_instrument_code"]),
                quantity_from=quantity_from,
                quantity_to=_to_decimal(row["quantity_to"]),
                cost_basis_transferred=average_price * quantity_from,
                cash_component=cash_component,
                comments=_optional_string(row.get("observations")),
            )
        )

    return records


def _load_frame(
    workbook: pd.ExcelFile,
    *,
    sheet_name: str,
    aliases: dict[str, tuple[str, ...]],
) -> pd.DataFrame:
    frame = cast(pd.DataFrame, workbook.parse(sheet_name))
    renamed_columns: dict[str, str] = {}
    missing: list[str] = []

    for canonical_name, options in aliases.items():
        for option in options:
            if option in frame.columns:
                renamed_columns[option] = canonical_name
                break
        else:
            missing.append(options[0])

    if missing:
        raise ValueError(
            f"Sheet {sheet_name!r} is missing expected column(s): {', '.join(missing)}"
        )

    return frame.rename(columns=renamed_columns)


def _build_source_record(
    *,
    batch: ImportBatch,
    workbook_path: Path,
    sheet_name: str,
    row_number: int,
) -> SourceRecord:
    return SourceRecord(
        batch_id=batch.batch_id,
        source_system=batch.source_system,
        source_file=str(workbook_path.resolve()),
        sheet_name=sheet_name,
        row_number=row_number,
        source_row_ref=f"{sheet_name}!{row_number}",
    )


def _map_transaction_type(value: object) -> TransactionType:
    try:
        return TRANSACTION_TYPE_MAP[str(value)]
    except KeyError as exc:
        raise ValueError(f"Unsupported transaction type: {value!r}") from exc


def _map_dividend_type(value: object) -> DividendType:
    try:
        return DIVIDEND_TYPE_MAP[str(value)]
    except KeyError as exc:
        raise ValueError(f"Unsupported dividend type: {value!r}") from exc


def _map_corporate_action_type(value: object) -> CorporateActionType:
    return CORPORATE_ACTION_TYPE_MAP.get(str(value), CorporateActionType.UNKNOWN)


def _map_instrument_type(value: object) -> InstrumentType:
    return INSTRUMENT_TYPE_MAP.get(str(value), InstrumentType.UNKNOWN)


def _compute_cash_effect(transaction_type: TransactionType, line_total: Decimal) -> Decimal:
    if transaction_type == TransactionType.BUY:
        return -line_total
    if transaction_type == TransactionType.SELL:
        return line_total
    return Decimal("0")


def _compute_cost_basis_effect(
    transaction_type: TransactionType,
    line_total: Decimal,
) -> Decimal | None:
    if transaction_type == TransactionType.BUY:
        return line_total
    if transaction_type == TransactionType.BONUS:
        return Decimal("0")
    if transaction_type == TransactionType.CONVERSION_IN:
        return line_total
    if transaction_type == TransactionType.CONVERSION_OUT:
        return -line_total
    return None


def _to_optional_date(value: object) -> date | None:
    if _is_missing_scalar(value):
        return None
    return _to_date(value)


def _to_date(value: object) -> date:
    parsed = pd.to_datetime(cast(Any, value), dayfirst=True, errors="raise")
    return parsed.date()


def _optional_string(value: object) -> str | None:
    if _is_missing_scalar(value):
        return None
    return str(value)


def _positive_decimal(value: Decimal) -> Decimal:
    return value if value > 0 else Decimal("0")


def _to_decimal(value: object) -> Decimal:
    if _is_missing_scalar(value):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, str):
        cleaned = re.sub(r"[^\d,.\-]", "", value.strip())
        if "," in cleaned and "." in cleaned:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        return Decimal(cleaned)
    return Decimal(str(value))


def _is_missing_scalar(value: object) -> bool:
    if value in ("", "-"):
        return True
    result = pd.isna(value)
    return bool(result) if isinstance(result, bool) else False


def _coerce_row_index(value: object) -> int:
    try:
        return int(str(value))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Unsupported row index: {value!r}") from exc
