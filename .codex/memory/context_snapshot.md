# CONTEXT SNAPSHOT

Generated: 2026-03-12 20:12 UTC

## Summary

# CONTEXT SUMMARY

- OV10 already has a stronger domain core than `final_kit`; `.codex/` is an auxiliary control plane.
- Trusted implementation path: `src/ov10/`; trusted validation path: `tests/`; trusted decisions: `docs/adr/`.
- Trusted environment: `.venv312`; do not treat the global Python 3.13 install as the primary path.
- Synthetic workbook generation now exists under `src/ov10/testing/` for controlled local scenarios.
- Workbook-based config loading now exists; the next high-value task is reducing `system_cash_account_used`.
- Monitor and watchdog scripts are operator-controlled automation, not mandatory background services.

## Full context excerpt

# CONTEXT

Date: 2026-03-12

## Current Repository State

- `src/ov10/` is the governed implementation path for the new OV10 core.
- `tests/` contains automated validation for ingestion, positions, cash, allocation, and persistence.
- `docs/adr/` is the canonical structural decision log.
- `docs/diagnostics/` holds reverse engineering evidence for the reference workbook, Apps Script, source benchmarks, and the multiagent plan.
- `docs/operations/SETUP_AND_USAGE.md` is the operator runbook for the current environment.
- `final_kit/` is a source of reusable autonomy scaffolding, not a higher-trust source than the OV10 repo itself.

## Current Working Capabilities

- ingest the current Status Invest style workbook into canonical facts
- persist governed import batches into SQLite with source lineage
- derive position snapshots with `average_cost_v1`
- derive broker and system cash ledgers and balance snapshots
- apply repo-versioned portfolio and book allocation rules
- load portfolio and book configuration from repo TOML or reference workbook sources
- generate deterministic synthetic input workbooks and scenario matrices for local testing
- inspect persisted batches through the CLI

## Current Operational Baseline

- trusted Python path: `.venv312`
- trusted database path: `var/ov10.sqlite3`
- current fixture: `data/OV10_base_2025.xlsx`
- current repo-versioned portfolio config: `config/ov10_portfolio.toml`

## Current Goals

1. preserve the existing stronger OV10 architecture and documentation
2. adopt the useful parts of `final_kit` as a control plane under `.codex/`
3. keep autonomy grounded in real backlog items and validation evidence
4. continue toward deeper parity after the first workbook-config adapter for `config.carteiras` and `config.books`

## Current Limitations

- the first spreadsheet configuration adapter exists, but workbook parity is still partial
- synthetic workbook generation exists for the current ingestion contract, but scenario breadth is still intentionally small
- one corporate action cash component still falls back to a system account
- reconciliation is still import-focused, not yet full reference-output parity
- fiscal outputs such as `darf` and `dirpf` are not implemented
- the remote payload loaded by the reference Apps Script has not been captured yet
- no CI pipeline exists yet

## Current Risks

- the reference solution still contains logic split between workbook formulas and remotely loaded Apps Script code
- `repo_monitor.py` can trigger repeated `codex continue` runs when `HEAD` changes frequently
- long-running watchdog automation can create noisy activity unless the backlog and state files stay disciplined
