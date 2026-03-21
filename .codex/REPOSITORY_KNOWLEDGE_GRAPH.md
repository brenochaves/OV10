# REPOSITORY KNOWLEDGE GRAPH

## Core edges

- `data/OV10_base_2025.xlsx`
  -> `src/ov10/ingestion/status_invest_xlsx.py`
  -> canonical facts with row-level lineage

- `src/ov10/ingestion/status_invest_xlsx.py`
  -> `src/ov10/domain/models.py`
  -> `src/ov10/services/import_batches.py`

- `src/ov10/services/import_batches.py`
  -> `src/ov10/positions/average_cost.py`
  -> `src/ov10/cash/derived.py`
  -> `src/ov10/config/portfolio_books.py`
  -> `src/ov10/allocation/portfolio_books.py`
  -> `src/ov10/storage/sqlite.py`

- `config/ov10_portfolio.toml`
  -> `src/ov10/config/portfolio_books.py`
  -> `src/ov10/allocation/portfolio_books.py`
  -> `book_position_snapshot`

- `src/ov10/cli.py`
  -> `src/ov10/services/import_batches.py`
  -> `src/ov10/storage/sqlite.py`
  -> operator JSON output

- `tests/test_status_invest_xlsx.py`
  -> validates workbook adapter and bundle shape

- `tests/test_position_engine.py`
  -> validates `average_cost_v1`

- `tests/test_cash_ledger.py`
  -> validates derived cash ledger behavior

- `tests/test_portfolio_allocation.py`
  -> validates portfolio and book routing

- `tests/test_persistence.py`
  -> validates end-to-end persistence and reporting flow

## Documentation edges

- `docs/diagnostics/2026-03-12_reverse_engineering_planilha.md`
  -> sheet inventory and reference workbook behavior map

- `docs/diagnostics/2026-03-12_reverse_engineering_appsscript.md`
  -> Apps Script inventory, remote-loader finding, and unresolved reverse-engineering gap

- `docs/diagnostics/2026-03-12_gap_analysis_ov10_vs_referencia.md`
  -> implementation priorities and missing capabilities

- `docs/diagnostics/2026-03-12_fontes_eventos_corporativos.md`
  -> external source benchmark backlog

- `docs/diagnostics/2026-03-12_plano_multiagente.md`
  -> specialist model aligned with the repo's workstreams

- `docs/operations/SETUP_AND_USAGE.md`
  -> operator commands, current environment, validation path, and `.codex` operational usage

- `.codex/INTEGRATION_REPORT.md`
  -> selective adoption record for `final_kit`

- `docs/adr/*.md`
  -> canonical architectural decisions

## Control-plane edges

- `.codex/BACKLOG.md`
  -> `.codex/TASK_GRAPH.md`
  -> next executable tasks for autonomous work

- `.codex/CONTEXT.md`
  -> `.codex/memory/context_summary.md`
  -> `.codex/memory/context_snapshot.md`

- `.codex/team/*.md`
  -> specialist roles for planning, review, testing, documentation, and domain research

- `.codex/scripts/repo_monitor.py`
  -> `git rev-parse HEAD`
  -> `codex continue` on head changes

- `.codex/scripts/watchdog_loop.ps1`
  -> periodic `codex continue` loop on Windows

## Excluded or downgraded sources

- `final_kit/`
  -> template source only
  -> not a higher-trust authority than current OV10 code and docs

- root-level legacy Python scripts
  -> exploratory references only
  -> not the governed implementation path
