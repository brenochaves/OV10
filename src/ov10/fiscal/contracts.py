from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from ov10.domain import DividendType, InstrumentType, TransactionType
from ov10.domain.models import CanonicalDividendReceipt, CanonicalTransaction
from ov10.fiscal.models import (
    DarfContractReport,
    DarfMonthlyBasis,
    DirpfAssetEntry,
    DirpfCarneLeaoEntry,
    DirpfContractReport,
    DirpfDebtEntry,
    DirpfExclusiveTaxIncomeEntry,
    DirpfTaxExemptIncomeEntry,
    FiscalContractReport,
    FiscalDependencyGap,
    FiscalSectionSupport,
)
from ov10.ingestion import load_status_invest_workbook
from ov10.positions import compute_positions

DARF_FIELD_ORDER = (
    "date",
    "acao_vol_alienacao",
    "etf_vol_alienacao",
    "opcao_vol_alienacao",
    "vol_alienacao",
    "acao_lucro_positivo",
    "acao_lucro_negativo",
    "isento_acao_20k",
    "isento_ativo_lucro",
    "acao_lucro",
    "etf_lucro",
    "ouro_lucro",
    "opcao_lucro",
    "dolar_fut_lucro",
    "indice_fut_lucro",
    "outros_fut_lucro",
    "termo_lucro",
    "nm_lucro",
    "nm_tributavel",
    "nm_imposto",
    "nm_irrf",
    "dt_acao_lucro",
    "dt_etf_lucro",
    "dt_ouro_lucro",
    "dt_opcao_lucro",
    "dt_dolar_fut_lucro",
    "dt_indice_fut_lucro",
    "dt_outros_fut_lucro",
    "dt_termo_lucro",
    "dt_lucro",
    "dt_tributavel",
    "dt_imposto",
    "dt_irrf",
    "nm_irrf_saldo",
    "dt_irrf_saldo",
)
DARF_SUPPORTED_FIELDS = (
    "date",
    "acao_vol_alienacao",
    "etf_vol_alienacao",
    "vol_alienacao",
)
DIRPF_BENS_DIREITOS_FIELDS = (
    "codigo",
    "localizacao",
    "cnpj",
    "descricao",
    "anterior",
    "atual",
)
DIRPF_DIVIDA_ONUS_FIELDS = (
    "codigo",
    "localizacao",
    "cnpj",
    "descricao",
    "anterior",
    "atual",
)
DIRPF_RENDIMENTOS_ISENTOS_FIELDS = (
    "codigo",
    "cnpj",
    "fonte_pagadora",
    "descricao",
    "valor",
)
DIRPF_TRIBUTACAO_EXCLUSIVA_FIELDS = (
    "codigo",
    "cnpj",
    "fonte_pagadora",
    "descricao",
    "valor",
)
DIRPF_CARNE_LEAO_FIELDS = (
    "date",
    "codigo",
    "descricao",
    "valor",
)
DIRPF_TAX_EXEMPT_TYPES = frozenset({DividendType.DIVIDEND, DividendType.INCOME})
DIRPF_TAX_EXEMPT_INSTRUMENTS = frozenset(
    {
        InstrumentType.STOCK_BR,
        InstrumentType.FII,
        InstrumentType.ETF_BR,
    }
)


def generate_fiscal_contract_report(
    source_workbook_path: str | Path,
) -> FiscalContractReport:
    source_workbook_path = Path(source_workbook_path)
    bundle = load_status_invest_workbook(source_workbook_path)
    positions = compute_positions(bundle.transactions)
    last_snapshot_date = max((item.snapshot_date for item in positions), default=None)
    base_year = _infer_dirpf_base_year(
        last_snapshot_date,
        bundle.transactions,
        bundle.dividend_receipts,
    )
    darf = _build_darf_contract(bundle.transactions)
    dirpf = _build_dirpf_contract(
        positions=positions,
        receipts=bundle.dividend_receipts,
        base_year=base_year,
    )
    gaps = _build_fiscal_gaps(
        positions=positions,
        transactions=bundle.transactions,
        receipts=bundle.dividend_receipts,
    )
    return FiscalContractReport(
        source_workbook=str(source_workbook_path.resolve()),
        batch_id=bundle.batch.batch_id,
        transaction_count=len(bundle.transactions),
        dividend_receipt_count=len(bundle.dividend_receipts),
        corporate_action_count=len(bundle.corporate_actions),
        snapshot_count=len(positions),
        darf=darf,
        dirpf=dirpf,
        gaps=gaps,
    )


def _infer_dirpf_base_year(
    last_snapshot_date: date | None,
    transactions: tuple[CanonicalTransaction, ...],
    receipts: tuple[CanonicalDividendReceipt, ...],
) -> int:
    if last_snapshot_date is not None:
        return last_snapshot_date.year
    years = [item.trade_date.year for item in transactions] + [
        item.received_date.year for item in receipts
    ]
    if years:
        return max(years)
    return date.today().year - 1


def _build_darf_contract(
    transactions: tuple[CanonicalTransaction, ...],
) -> DarfContractReport:
    sale_buckets: dict[date, dict[str, Decimal]] = defaultdict(
        lambda: {
            "stock_sale_volume": Decimal("0"),
            "etf_sale_volume": Decimal("0"),
            "total_sale_volume": Decimal("0"),
        }
    )
    start_year = min((item.trade_date.year for item in transactions), default=date.today().year)
    for item in transactions:
        if item.transaction_type is not TransactionType.SELL:
            continue
        month_end = _month_end(item.trade_date)
        gross_amount = abs(item.gross_amount)
        bucket = sale_buckets[month_end]
        bucket["total_sale_volume"] += gross_amount
        if item.instrument_type is InstrumentType.STOCK_BR:
            bucket["stock_sale_volume"] += gross_amount
        elif item.instrument_type is InstrumentType.ETF_BR:
            bucket["etf_sale_volume"] += gross_amount

    rows = tuple(
        DarfMonthlyBasis(
            month_end=month_end,
            stock_sale_volume=payload["stock_sale_volume"],
            etf_sale_volume=payload["etf_sale_volume"],
            option_sale_volume=None,
            total_sale_volume=payload["total_sale_volume"],
        )
        for month_end, payload in sorted(sale_buckets.items())
    )
    unsupported_fields = tuple(
        item for item in DARF_FIELD_ORDER if item not in set(DARF_SUPPORTED_FIELDS)
    )
    return DarfContractReport(
        start_year=start_year,
        investor_slot_range="A9:A15",
        worksheet_header_range="C5:AK5",
        field_order=DARF_FIELD_ORDER,
        supported_fields=DARF_SUPPORTED_FIELDS,
        unsupported_fields=unsupported_fields,
        monthly_rows=rows,
    )


def _build_dirpf_contract(
    *,
    positions: list,
    receipts: tuple[CanonicalDividendReceipt, ...],
    base_year: int,
) -> DirpfContractReport:
    asset_entries = tuple(
        DirpfAssetEntry(
            base_year=base_year,
            instrument_code=item.instrument_code,
            tax_code=None,
            location_code=None,
            cnpj=None,
            description=f"Posicao aberta em {item.instrument_code}",
            previous_amount=None,
            current_amount=item.total_cost,
            snapshot_date=item.snapshot_date,
        )
        for item in positions
        if item.snapshot_date.year == base_year
    )
    tax_exempt_income_entries = _build_dirpf_tax_exempt_entries(
        receipts=receipts,
        base_year=base_year,
    )
    exclusive_tax_income_entries = _build_dirpf_exclusive_income_entries(
        receipts=receipts,
        base_year=base_year,
    )
    debt_entries: tuple[DirpfDebtEntry, ...] = ()
    carne_leao_entries: tuple[DirpfCarneLeaoEntry, ...] = ()
    section_support = (
        FiscalSectionSupport(
            section_id="bens_direitos",
            worksheet_range="D4:I",
            field_order=DIRPF_BENS_DIREITOS_FIELDS,
            support_level="partial",
            candidate_count=len(asset_entries),
            current_source="position_snapshots",
            note=(
                "As posicoes abertas ja geram candidatos para bens e direitos, "
                "mas ainda faltam codigo fiscal, localizacao, CNPJ e valor anterior."
            ),
        ),
        FiscalSectionSupport(
            section_id="divida_onus",
            worksheet_range="L4:Q",
            field_order=DIRPF_DIVIDA_ONUS_FIELDS,
            support_level="missing",
            candidate_count=0,
            current_source="",
            note="O OV10 ainda nao tem entrada canonica para dividas e onus.",
        ),
        FiscalSectionSupport(
            section_id="rendimentos_isentos",
            worksheet_range="T4:X",
            field_order=DIRPF_RENDIMENTOS_ISENTOS_FIELDS,
            support_level="partial",
            candidate_count=len(tax_exempt_income_entries),
            current_source="canonical_dividend_receipt filtered by BR exempt-like receipts",
            note=(
                "Ha candidatos de rendimentos isentos a partir de proventos BR nao-JCP, "
                "mas a classificacao fiscal ainda nao esta completa."
            ),
        ),
        FiscalSectionSupport(
            section_id="tributacao_exclusiva",
            worksheet_range="AA4:AE",
            field_order=DIRPF_TRIBUTACAO_EXCLUSIVA_FIELDS,
            support_level="partial",
            candidate_count=len(exclusive_tax_income_entries),
            current_source="canonical_dividend_receipt[JCP]",
            note=(
                "JCP ja gera candidatos objetivos para tributacao exclusiva, "
                "mas ainda faltam mapeamentos de codigo/CNPJ."
            ),
        ),
        FiscalSectionSupport(
            section_id="carne_leao",
            worksheet_range="AH4:AK",
            field_order=DIRPF_CARNE_LEAO_FIELDS,
            support_level="missing",
            candidate_count=0,
            current_source="",
            note="O OV10 ainda nao tem entrada canonica para carne-leao manual.",
        ),
    )
    return DirpfContractReport(
        base_year=base_year,
        investor_slot_range="A7:A13",
        asset_entries=asset_entries,
        debt_entries=debt_entries,
        tax_exempt_income_entries=tax_exempt_income_entries,
        exclusive_tax_income_entries=exclusive_tax_income_entries,
        carne_leao_entries=carne_leao_entries,
        section_support=section_support,
    )


def _build_dirpf_tax_exempt_entries(
    *,
    receipts: tuple[CanonicalDividendReceipt, ...],
    base_year: int,
) -> tuple[DirpfTaxExemptIncomeEntry, ...]:
    totals: dict[tuple[str, str], Decimal] = defaultdict(lambda: Decimal("0"))
    for item in receipts:
        if item.received_date.year != base_year:
            continue
        if item.dividend_type not in DIRPF_TAX_EXEMPT_TYPES:
            continue
        if item.instrument_type not in DIRPF_TAX_EXEMPT_INSTRUMENTS:
            continue
        key = (item.instrument_code, item.dividend_type.value)
        totals[key] += item.net_amount

    return tuple(
        DirpfTaxExemptIncomeEntry(
            base_year=base_year,
            tax_code=None,
            payer_cnpj=None,
            payer_name=None,
            description=f"{dividend_type} {instrument_code}",
            amount=amount,
        )
        for (instrument_code, dividend_type), amount in sorted(totals.items())
    )


def _build_dirpf_exclusive_income_entries(
    *,
    receipts: tuple[CanonicalDividendReceipt, ...],
    base_year: int,
) -> tuple[DirpfExclusiveTaxIncomeEntry, ...]:
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for item in receipts:
        if item.received_date.year != base_year:
            continue
        if item.dividend_type is not DividendType.JCP:
            continue
        totals[item.instrument_code] += item.net_amount

    return tuple(
        DirpfExclusiveTaxIncomeEntry(
            base_year=base_year,
            tax_code=None,
            payer_cnpj=None,
            payer_name=None,
            description=f"JCP {instrument_code}",
            amount=amount,
        )
        for instrument_code, amount in sorted(totals.items())
    )


def _build_fiscal_gaps(
    *,
    positions: list,
    transactions: tuple[CanonicalTransaction, ...],
    receipts: tuple[CanonicalDividendReceipt, ...],
) -> tuple[FiscalDependencyGap, ...]:
    sell_count = sum(item.transaction_type is TransactionType.SELL for item in transactions)
    return (
        FiscalDependencyGap(
            code="missing_tax_lot_engine",
            severity="high",
            summary="DARF gain and tax fields still lack a tax-lot engine.",
            affected_outputs=("darf",),
            note=(
                f"O contrato fiscal ja enxerga {sell_count} vendas, mas ainda nao existe "
                "motor de ganho realizado com lotes fiscais, compensacao de prejuizo, "
                "IRRF e imposto devido."
            ),
        ),
        FiscalDependencyGap(
            code="unsupported_tax_asset_classes",
            severity="high",
            summary="Current instrument taxonomy does not yet cover all DARF classes.",
            affected_outputs=("darf",),
            note=(
                "O workbook fiscal espera opcoes, ouro, futuro dolar, futuro indice, "
                "outros futuros e termo; esses eixos ainda nao existem no dominio canonico."
            ),
        ),
        FiscalDependencyGap(
            code="missing_dirpf_tax_code_mapping",
            severity="medium",
            summary="DIRPF entries still lack tax code, location, and payer mapping.",
            affected_outputs=("dirpf",),
            note=(
                f"O OV10 ja consegue gerar {len(positions)} candidatos de bens e direitos "
                f"e {len(receipts)} fatos de proventos, mas ainda nao possui tabela "
                "governada de codigo fiscal/localizacao/CNPJ."
            ),
        ),
        FiscalDependencyGap(
            code="missing_prior_year_fiscal_snapshot",
            severity="medium",
            summary="DIRPF previous-year amounts cannot be reproduced yet.",
            affected_outputs=("dirpf",),
            note=(
                "O contrato atual so tem o snapshot aberto corrente; valores `anterior` "
                "exigem snapshot fiscal de fechamento do ano-base anterior."
            ),
        ),
        FiscalDependencyGap(
            code="missing_manual_fiscal_inputs",
            severity="medium",
            summary="Liabilities and carne-leao remain outside the current ingestion path.",
            affected_outputs=("dirpf",),
            note=(
                "As secoes `divida_onus` e `carne_leao` dependem de entradas manuais que "
                "ainda nao existem no pipeline canonico."
            ),
        ),
    )


def _month_end(value: date) -> date:
    return date(value.year, value.month, monthrange(value.year, value.month)[1])
