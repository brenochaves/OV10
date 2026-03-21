# ARCHITECTURE MAP

## Top-level modules

- `src/ov10/domain`
  - purpose: canonical enums and models for transactions, dividends, corporate actions, cash, positions, and allocation entities
  - depends_on: Python standard library only
  - exposes: durable contracts used across ingestion, services, storage, and computation

- `src/ov10/ingestion`
  - purpose: translate source workbooks into canonical bundles with lineage
  - depends_on: `ov10.domain`, pandas, openpyxl
  - exposes: `load_status_invest_workbook`

- `src/ov10/positions`
  - purpose: compute open positions from canonical transactions
  - depends_on: `ov10.domain`
  - exposes: `compute_positions`, `POSITION_ENGINE_VERSION`

- `src/ov10/cash`
  - purpose: derive cash movements and balances from canonical facts
  - depends_on: `ov10.domain`
  - exposes: derived cash ledger functions

- `src/ov10/config`
  - purpose: load governed repo-versioned configuration
  - depends_on: `ov10.domain`, TOML parsing through the standard library
  - exposes: portfolio and book configuration loading

- `src/ov10/allocation`
  - purpose: route accounts and position snapshots into portfolios and books
  - depends_on: `ov10.domain`, `ov10.config`
  - exposes: allocation and projection helpers

- `src/ov10/services`
  - purpose: orchestrate end-to-end workflows such as persisted workbook imports
  - depends_on: ingestion, positions, cash, config, allocation, storage
  - exposes: `persist_status_invest_xlsx`

- `src/ov10/storage`
  - purpose: local-first governed persistence
  - depends_on: `sqlite3`, `ov10.domain`
  - exposes: `SQLiteOV10Store`, database initialization, fetch and report flows

- `src/ov10/cli.py`
  - purpose: operator-facing JSON CLI
  - depends_on: services, storage, ingestion, positions
  - exposes: `ov10` command and module execution path

## Critical paths

- `data/OV10_base_2025.xlsx -> ov10.ingestion.status_invest_xlsx -> canonical bundle`
  - behavior: parse workbook tabs into transactions, dividend receipts, corporate actions, and source-row lineage
  - risks: source workbook semantics can drift and some reference behavior still lives outside the current cloneable artifacts

- `canonical facts -> ov10.services.import_batches -> ov10.storage.sqlite`
  - behavior: persist governed import batches, source records, mappings, reconciliation, cash, and position snapshots
  - risks: incorrect idempotency or schema drift would compromise reproducibility

- `canonical transactions -> ov10.positions.average_cost`
  - behavior: compute reproducible open positions using `average_cost_v1`
  - risks: future rule expansion for corporate actions, taxes, or multi-book semantics must preserve backward traceability

- `config/ov10_portfolio.toml -> ov10.config.portfolio_books -> ov10.allocation.portfolio_books`
  - behavior: load portfolio and book routing rules and project account snapshots into book snapshots
  - risks: the TOML baseline is conservative and intentionally temporary until workbook-config import exists

- `.codex/* -> operator or autonomous Codex sessions`
  - behavior: store durable memory, backlog, prompts, and operational scripts
  - risks: if kept out of sync with actual code and ADRs, it becomes misleading rather than useful

## Data flow notes

- source: `data/OV10_base_2025.xlsx`
  - transformation: workbook adapter parses tabs into canonical domain objects and bundle summaries
  - sink: CLI summaries and persisted import batches

- source: canonical facts
  - transformation: service layer derives positions, cash, mappings, reconciliation, and allocation projections
  - sink: SQLite tables and JSON CLI reports

- source: `docs/diagnostics/`
  - transformation: reverse engineering evidence informs ADRs and backlog priorities
  - sink: architecture direction and next implementation tasks

- source: `final_kit/`
  - transformation: useful autonomy scaffolding is selectively adapted under `.codex/`
  - sink: project-specific control plane and operator automation
