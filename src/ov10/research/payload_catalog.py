from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FUNCTION_PATTERN = re.compile(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")

SHEET_DESCRIPTOR_FUNCTIONS = {
    "Historico",
    "AtivosPonto",
    "PortfolioPonto",
    "ConfigParametros",
    "FundamentusPonto",
    "FundsExplorerPonto",
    "Extratos",
    "OperacoesProventos",
    "LeiaMe",
    "Radar",
    "Rendimentos",
    "Analise",
    "Alocacao",
    "Carteira",
    "DashboardPonto",
    "CarteirasPonto",
    "CarteirasPontoPonto",
    "Portfolio",
    "ConfigOutros",
    "ConfigCarteiras",
    "ConfigBooks",
    "Summary",
    "Caixa",
    "Scripts",
    "DARF",
    "DIRPF",
    "Config",
}

MODULE_ORDER = [
    "sheet_descriptors",
    "update_and_migration",
    "import_export_backup",
    "portfolio_positions",
    "dividends_income",
    "cash_brokers",
    "allocation_books",
    "fiscal",
    "market_data_external",
    "alpha_licensing",
    "ui_and_menu",
    "utilities",
]

MODULE_DESCRIPTIONS = {
    "sheet_descriptors": "Workbook sheet contracts and named-range descriptors.",
    "update_and_migration": "Version checks, workbook upgrades, layout resets, and migrations.",
    "import_export_backup": (
        "JSON import/export, backups, previous-workbook migration, and file operations."
    ),
    "portfolio_positions": "Operations, positions, pricing, TIR, and portfolio calculations.",
    "dividends_income": "Dividends, proventos, and income-oriented calculations.",
    "cash_brokers": "Cash ledger, broker routing, CEI/Avenue imports, and statement processing.",
    "allocation_books": "Portfolio allocation, books, carteiras, and summary orchestration.",
    "fiscal": "DARF, DIRPF, tax-specific calculations, and tax report scaffolding.",
    "market_data_external": "External market-data integrations and indicator refresh flows.",
    "alpha_licensing": "Alpha-user licensing, resource validation, and copy-count controls.",
    "ui_and_menu": "HTML/menu entrypoints and interactive dialogs.",
    "utilities": "Generic helpers or uncategorized support functions.",
}

EVIDENCE_PATTERNS = {
    "PLANOS_USUARIOS_ALPHA": r"PLANOS_USUARIOS_ALPHA",
    "RECURSOS_USUARIOS_ALPHA": r"RECURSOS_USUARIOS_ALPHA",
    "UrlFetchApp.fetch": r"UrlFetchApp\.fetch",
    "GOOGLEFINANCE": r"GOOGLEFINANCE",
    "fundamentus": r"fundamentus",
    "stockinfo": r"stockinfo",
}

HIGH_VALUE_MODULES = [
    "portfolio_positions",
    "dividends_income",
    "cash_brokers",
    "allocation_books",
    "fiscal",
    "alpha_licensing",
]

LOW_VALUE_MODULES = [
    "ui_and_menu",
    "utilities",
]

SELECTED_REFERENCE_FUNCTIONS = [
    "verificarAtualizacoes",
    "atualizarVersao",
    "obterOperacoesProventosJSON",
    "obterConfigBooksJSON",
    "obterCaixaJSON",
    "obterConfigCarteirasJSON",
    "portfolioDefinirAtivos",
    "portfolioOrdenarMatriz",
    "importarExtratoAvenue",
    "importarExtratoCEI",
    "transferirCEICorretorasOperacoesProventos",
    "obterTratarCorretoraInvestidor",
    "ativarConfigBooks",
    "ativarCaixa",
    "ativarRendimentos",
    "ativarSummary",
    "ativarDARF",
    "ativarDIRPF",
    "calcularDARF",
    "calcularDIRPF",
    "validarIDPlanilha",
    "validarRecursoUsuarioAlpha",
    "getStockinfoApi",
    "atualizarIndicadores",
    "calcularTIR",
    "atualizarTIR",
]


@dataclass(frozen=True)
class FunctionCatalogEntry:
    name: str
    line: int
    modules: tuple[str, ...]


def extract_function_catalog_entries(payload_text: str) -> list[FunctionCatalogEntry]:
    entries: list[FunctionCatalogEntry] = []
    seen: set[str] = set()
    for match in FUNCTION_PATTERN.finditer(payload_text):
        name = match.group(1)
        if name in seen:
            continue
        seen.add(name)
        line = payload_text.count("\n", 0, match.start()) + 1
        modules = tuple(classify_function(name))
        entries.append(FunctionCatalogEntry(name=name, line=line, modules=modules))
    return entries


def classify_function(name: str) -> list[str]:
    lower_name = name.lower()
    modules: list[str] = []

    if name in SHEET_DESCRIPTOR_FUNCTIONS:
        modules.append("sheet_descriptors")

    if (
        "alpha" in lower_name
        or "usuarioalpha" in lower_name
        or "validaridplanilha" in lower_name
        or "recursousuarioalpha" in lower_name
        or "ownerplanilha" in lower_name
        or "planilhausuarioalpha" in lower_name
        or "revogar" in lower_name
        or "numerocopiasplanilhaspermitido" in lower_name
    ):
        modules.append("alpha_licensing")

    if (
        "darf" in lower_name
        or "dirpf" in lower_name
        or "carneleao" in lower_name
        or "tribut" in lower_name
        or "isent" in lower_name
        or "impost" in lower_name
    ):
        modules.append("fiscal")

    if (
        "carteira" in lower_name
        or "book" in lower_name
        or "alocacao" in lower_name
        or "summary" in lower_name
        or "dashboard" in lower_name
    ):
        modules.append("allocation_books")

    if (
        "provento" in lower_name
        or "rendimento" in lower_name
        or "divid" in lower_name
        or "jscp" in lower_name
    ):
        modules.append("dividends_income")

    if (
        "caixa" in lower_name
        or "extrato" in lower_name
        or "corretora" in lower_name
        or "cei" in lower_name
        or "saldo" in lower_name
    ):
        modules.append("cash_brokers")

    if (
        "portfolio" in lower_name
        or "ativo" in lower_name
        or "operac" in lower_name
        or "trade" in lower_name
        or "cotacao" in lower_name
        or "tir" in lower_name
    ):
        modules.append("portfolio_positions")

    if (
        "fundamentus" in lower_name
        or "stockinfo" in lower_name
        or "yahoo" in lower_name
        or "indicadores" in lower_name
        or "noticias" in lower_name
        or "moeda" in lower_name
    ):
        modules.append("market_data_external")

    if (
        lower_name.startswith("html_")
        or lower_name.startswith("ativar")
        or name
        in {
            "definirMenuHTML",
            "mensagemUsuario",
            "obterConfirmacaoUsuarioYESNO",
            "obterRespostaUsuarioOKCANCEL",
        }
    ):
        modules.append("ui_and_menu")

    if (
        "atualiz" in lower_name
        or "versao" in lower_name
        or "padrao" in lower_name
        or "limparconteudoaba" in lower_name
        or "ajustarconfiguracoes" in lower_name
        or "migr" in lower_name
        or "trigger" in lower_name
        or "desligaronoff" in lower_name
        or "ligaronoff" in lower_name
        or "excluirabasinvalidas" in lower_name
        or "intervalo" in lower_name
        or "layout" in lower_name
    ):
        modules.append("update_and_migration")

    if (
        "import" in lower_name
        or "export" in lower_name
        or "backup" in lower_name
        or "download" in lower_name
        or "salvararquivo" in lower_name
        or "csvtojson" in lower_name
        or "pdf" in lower_name
        or "restaurarparametros" in lower_name
        or "salvarparametros" in lower_name
    ):
        modules.append("import_export_backup")

    if not modules:
        modules.append("utilities")

    return [module for module in MODULE_ORDER if module in modules]


def build_remote_payload_catalog(
    payload_text: str,
    payload_path: Path | None = None,
) -> dict[str, Any]:
    entries = extract_function_catalog_entries(payload_text)
    module_entries: dict[str, list[FunctionCatalogEntry]] = {module: [] for module in MODULE_ORDER}
    for entry in entries:
        for module in entry.modules:
            module_entries[module].append(entry)

    evidence_markers = {}
    for label, pattern in EVIDENCE_PATTERNS.items():
        match = re.search(pattern, payload_text)
        if match is None:
            continue
        evidence_markers[label] = {
            "line": payload_text.count("\n", 0, match.start()) + 1,
            "pattern": pattern,
        }

    selected_references = {}
    entry_by_name = {entry.name: entry for entry in entries}
    for name in SELECTED_REFERENCE_FUNCTIONS:
        entry = entry_by_name.get(name)
        if entry is None:
            continue
        selected_references[name] = {
            "line": entry.line,
            "modules": list(entry.modules),
        }

    module_summary = {}
    for module in MODULE_ORDER:
        module_summary[module] = {
            "description": MODULE_DESCRIPTIONS[module],
            "count": len(module_entries[module]),
            "sample_functions": [entry.name for entry in module_entries[module][:15]],
        }

    return {
        "payloadPath": str(payload_path.resolve()) if payload_path is not None else None,
        "functionCount": len(entries),
        "moduleSummary": module_summary,
        "highValueModules": HIGH_VALUE_MODULES,
        "lowValueModules": LOW_VALUE_MODULES,
        "selectedReferences": selected_references,
        "evidenceMarkers": evidence_markers,
        "entries": [
            {
                "name": entry.name,
                "line": entry.line,
                "modules": list(entry.modules),
            }
            for entry in entries
        ],
    }


def analyze_remote_script_artifact(
    payload_path: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    payload_text = payload_path.read_text(encoding="utf-8")
    catalog = build_remote_payload_catalog(payload_text, payload_path=payload_path)
    resolved_output_path = output_path or payload_path.with_suffix(".catalog.json")
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return catalog
