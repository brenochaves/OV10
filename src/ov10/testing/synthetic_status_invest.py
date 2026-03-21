from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

OPERATIONS_SHEET = "Operacoes"
DIVIDENDS_SHEET = "Proventos"
CORPORATE_ACTIONS_SHEET = "Conversoes_Mapeadas"

OPERATIONS_COLUMNS = [
    "NEGOCIACAO",
    "ORDEM",
    "Ativo",
    "CATEGORIA",
    "BROKER",
    "QUANTIDADE",
    "PRECO",
    "TOTAL",
]
DIVIDENDS_COLUMNS = [
    "Data_com",
    "Pagamento",
    "Ativo",
    "CATEGORIA",
    "Corretora_banco",
    "Tipo",
    "Quantidade",
    "Total",
    "Total_liq",
]
CORPORATE_ACTIONS_COLUMNS = [
    "Data_Conversao",
    "Tipo_Conversao",
    "Ativo_De",
    "Ativo_Para",
    "Quantidade_De",
    "Quantidade_Para",
    "Preco_Medio",
    "Valor_Retornado",
    "Observacoes",
]


@dataclass(frozen=True, slots=True)
class SyntheticTransactionRow:
    trade_date: date
    order: str
    instrument_code: str
    category: str
    broker_name: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal


@dataclass(frozen=True, slots=True)
class SyntheticDividendRow:
    payment_date: date
    instrument_code: str
    category: str
    broker_name: str
    dividend_type: str
    quantity: Decimal
    gross_amount: Decimal
    net_amount: Decimal
    reference_date: date | None = None


@dataclass(frozen=True, slots=True)
class SyntheticCorporateActionRow:
    effective_date: date
    action_type: str
    source_instrument_code: str
    target_instrument_code: str
    quantity_from: Decimal
    quantity_to: Decimal
    average_price: Decimal
    cash_component: Decimal = Decimal("0")
    observations: str | None = None


@dataclass(frozen=True, slots=True)
class SyntheticStatusInvestScenario:
    name: str
    description: str
    transactions: tuple[SyntheticTransactionRow, ...]
    dividend_receipts: tuple[SyntheticDividendRow, ...]
    corporate_actions: tuple[SyntheticCorporateActionRow, ...]

    def summary(self) -> dict[str, object]:
        return {
            "scenario": self.name,
            "description": self.description,
            "transactions": len(self.transactions),
            "dividend_receipts": len(self.dividend_receipts),
            "corporate_actions": len(self.corporate_actions),
        }


def list_synthetic_status_invest_scenarios() -> list[str]:
    return sorted(_SCENARIOS)


def build_synthetic_status_invest_workbook(
    output_path: str | Path,
    *,
    scenario_name: str,
) -> dict[str, object]:
    try:
        scenario = _SCENARIOS[scenario_name]
    except KeyError as exc:
        raise ValueError(f"Unknown synthetic scenario: {scenario_name}") from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    operations_frame = pd.DataFrame(
        [_transaction_to_row(item) for item in scenario.transactions],
        columns=pd.Index(OPERATIONS_COLUMNS),
    )
    dividends_frame = pd.DataFrame(
        [_dividend_to_row(item) for item in scenario.dividend_receipts],
        columns=pd.Index(DIVIDENDS_COLUMNS),
    )
    corporate_actions_frame = pd.DataFrame(
        [_corporate_action_to_row(item) for item in scenario.corporate_actions],
        columns=pd.Index(CORPORATE_ACTIONS_COLUMNS),
    )

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        operations_frame.to_excel(writer, sheet_name=OPERATIONS_SHEET, index=False)
        dividends_frame.to_excel(writer, sheet_name=DIVIDENDS_SHEET, index=False)
        corporate_actions_frame.to_excel(writer, sheet_name=CORPORATE_ACTIONS_SHEET, index=False)

    return {
        **scenario.summary(),
        "output_path": str(path.resolve()),
    }


def generate_synthetic_status_invest_matrix(output_dir: str | Path) -> list[dict[str, object]]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    reports: list[dict[str, object]] = []
    for scenario_name in list_synthetic_status_invest_scenarios():
        output_path = target_dir / f"{scenario_name}.xlsx"
        reports.append(
            build_synthetic_status_invest_workbook(
                output_path,
                scenario_name=scenario_name,
            )
        )
    return reports


def _transaction_to_row(item: SyntheticTransactionRow) -> dict[str, object]:
    return {
        "NEGOCIACAO": _format_date(item.trade_date),
        "ORDEM": item.order,
        "Ativo": item.instrument_code,
        "CATEGORIA": item.category,
        "BROKER": item.broker_name,
        "QUANTIDADE": _decimal_to_str(item.quantity),
        "PRECO": _decimal_to_str(item.unit_price),
        "TOTAL": _decimal_to_str(item.total),
    }


def _dividend_to_row(item: SyntheticDividendRow) -> dict[str, object]:
    return {
        "Data_com": None if item.reference_date is None else _format_date(item.reference_date),
        "Pagamento": _format_date(item.payment_date),
        "Ativo": item.instrument_code,
        "CATEGORIA": item.category,
        "Corretora_banco": item.broker_name,
        "Tipo": item.dividend_type,
        "Quantidade": _decimal_to_str(item.quantity),
        "Total": _decimal_to_str(item.gross_amount),
        "Total_liq": _decimal_to_str(item.net_amount),
    }


def _corporate_action_to_row(item: SyntheticCorporateActionRow) -> dict[str, object]:
    return {
        "Data_Conversao": _format_date(item.effective_date),
        "Tipo_Conversao": item.action_type,
        "Ativo_De": item.source_instrument_code,
        "Ativo_Para": item.target_instrument_code,
        "Quantidade_De": _decimal_to_str(item.quantity_from),
        "Quantidade_Para": _decimal_to_str(item.quantity_to),
        "Preco_Medio": _decimal_to_str(item.average_price),
        "Valor_Retornado": _decimal_to_str(item.cash_component),
        "Observacoes": item.observations,
    }


def _decimal_to_str(value: Decimal) -> str:
    return str(value)


def _format_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _scenario_base() -> SyntheticStatusInvestScenario:
    return SyntheticStatusInvestScenario(
        name="base",
        description="Single broker flow with buy, sell, dividend, and no corporate action cash.",
        transactions=(
            SyntheticTransactionRow(
                trade_date=date(2025, 1, 10),
                order="Compra",
                instrument_code="ABC3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("100"),
                unit_price=Decimal("10"),
                total=Decimal("1000"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 2, 5),
                order="Venda",
                instrument_code="ABC3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("40"),
                unit_price=Decimal("12"),
                total=Decimal("480"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 3, 3),
                order="Compra",
                instrument_code="TESOURO-SELIC",
                category="Tesouro",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("1"),
                unit_price=Decimal("950"),
                total=Decimal("950"),
            ),
        ),
        dividend_receipts=(
            SyntheticDividendRow(
                reference_date=date(2025, 2, 20),
                payment_date=date(2025, 3, 15),
                instrument_code="ABC3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                dividend_type="Dividendo",
                quantity=Decimal("60"),
                gross_amount=Decimal("30"),
                net_amount=Decimal("30"),
            ),
        ),
        corporate_actions=(),
    )


def _scenario_corporate_action_cash_unassigned() -> SyntheticStatusInvestScenario:
    return SyntheticStatusInvestScenario(
        name="corporate_action_cash_unassigned",
        description=(
            "Legacy-named scenario with unique same-day conversion evidence, useful "
            "for positive broker-attribution tests."
        ),
        transactions=(
            SyntheticTransactionRow(
                trade_date=date(2025, 4, 1),
                order="Compra",
                instrument_code="ABC3",
                category="AÃ§Ãµes",
                broker_name="INTER DTVM LTDA",
                quantity=Decimal("100"),
                unit_price=Decimal("10"),
                total=Decimal("1000"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 5, 20),
                order="ConversÃ£o (S)",
                instrument_code="VAMO3",
                category="AÃ§Ãµes",
                broker_name="INTER DTVM LTDA",
                quantity=Decimal("100"),
                unit_price=Decimal("10"),
                total=Decimal("1000"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 5, 20),
                order="ConversÃ£o (E)",
                instrument_code="AMOB3",
                category="AÃ§Ãµes",
                broker_name="INTER DTVM LTDA",
                quantity=Decimal("100"),
                unit_price=Decimal("10"),
                total=Decimal("1000"),
            ),
        ),
        dividend_receipts=(),
        corporate_actions=(
            SyntheticCorporateActionRow(
                effective_date=date(2025, 5, 20),
                action_type="ConversÃ£o Simples",
                source_instrument_code="VAMO3",
                target_instrument_code="AMOB3",
                quantity_from=Decimal("100"),
                quantity_to=Decimal("100"),
                average_price=Decimal("10"),
                cash_component=Decimal("12.50"),
                observations="synthetic conversion with residual cash",
            ),
        ),
    )


def _scenario_corporate_action_cash_ambiguous() -> SyntheticStatusInvestScenario:
    return SyntheticStatusInvestScenario(
        name="corporate_action_cash_ambiguous",
        description=(
            "Corporate action cash with multiple brokers touching the source instrument, "
            "useful for ambiguity tests."
        ),
        transactions=(
            SyntheticTransactionRow(
                trade_date=date(2025, 1, 15),
                order="Compra",
                instrument_code="ZZZ3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("50"),
                unit_price=Decimal("20"),
                total=Decimal("1000"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 2, 10),
                order="Compra",
                instrument_code="ZZZ3",
                category="AÃ§Ãµes",
                broker_name="INTER DTVM LTDA",
                quantity=Decimal("50"),
                unit_price=Decimal("22"),
                total=Decimal("1100"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 6, 1),
                order="ConversÃ£o (S)",
                instrument_code="ZZZ3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("50"),
                unit_price=Decimal("21"),
                total=Decimal("1050"),
            ),
            SyntheticTransactionRow(
                trade_date=date(2025, 6, 1),
                order="ConversÃ£o (E)",
                instrument_code="YYY3",
                category="AÃ§Ãµes",
                broker_name="XP INVESTIMENTOS CCTVM S/A",
                quantity=Decimal("50"),
                unit_price=Decimal("21"),
                total=Decimal("1050"),
            ),
        ),
        dividend_receipts=(
            SyntheticDividendRow(
                payment_date=date(2025, 4, 15),
                instrument_code="ZZZ3",
                category="AÃ§Ãµes",
                broker_name="INTER DTVM LTDA",
                dividend_type="JCP",
                quantity=Decimal("50"),
                gross_amount=Decimal("8"),
                net_amount=Decimal("6.8"),
                reference_date=date(2025, 4, 1),
            ),
        ),
        corporate_actions=(
            SyntheticCorporateActionRow(
                effective_date=date(2025, 6, 1),
                action_type="IncorporaÃ§Ã£o Total",
                source_instrument_code="ZZZ3",
                target_instrument_code="YYY3",
                quantity_from=Decimal("50"),
                quantity_to=Decimal("50"),
                average_price=Decimal("21"),
                cash_component=Decimal("3.25"),
                observations="synthetic ambiguous broker attribution case",
            ),
        ),
    )


_SCENARIOS: dict[str, SyntheticStatusInvestScenario] = {
    scenario.name: scenario
    for scenario in (
        _scenario_base(),
        _scenario_corporate_action_cash_unassigned(),
        _scenario_corporate_action_cash_ambiguous(),
    )
}
