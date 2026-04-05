# CONTEXT

Date: 2026-04-05

## Current Repository State

- `src/ov10/` is the governed implementation path for the new OV10 core.
- `src/ov10/reference/` now contains the first governed instrument identity layer.
- `src/ov10/market/` now contains governed market and FX snapshot contracts plus public-source adapters.
- `tests/` contains automated validation for ingestion, positions, cash, allocation, and persistence.
- `docs/adr/` is the canonical structural decision log.
- `docs/diagnostics/` holds reverse engineering evidence for the reference workbook, Apps Script, source benchmarks, and the multiagent plan.
- `docs/operations/SETUP_AND_USAGE.md` is the operator runbook for the current environment.
- `docs/operations/GIT_CHECKPOINT_POLICY.md` governs repository checkpoint cadence and sync hygiene.
- root `.codex/` is the active autonomy/control plane, and `archive/` is historical only.
- `.codex/EXECUTION_LEDGER.md` separates delivered work from approved-but-not-yet-executed workstreams.

## Current Working Capabilities

- ingest the current Status Invest style workbook into canonical facts
- persist governed import batches into SQLite with source lineage
- derive position snapshots with `average_cost_v1`
- derive broker and system cash ledgers and balance snapshots
- apply repo-versioned portfolio and book allocation rules
- load portfolio and book configuration from repo TOML or reference workbook sources
- generate deterministic synthetic input workbooks and scenario matrices for local testing
- inspect persisted batches through the CLI
- inspect canonical instrument identity through `instrument-reference-report`
- refresh and inspect governed market and FX snapshots through dedicated CLI paths
- consume persisted market and FX snapshots inside valuation-aware reference reconciliation when a database is supplied
- inspect first-pass fiscal output contracts for `darf` and `dirpf` through a governed CLI report
- run the governed quality stack locally and in CI, including type checking, config validation, SQL lint, dependency audit, and `pre-commit`
- run a governed Git sync audit and scheduled reminder path for repository checkpoint hygiene

## Current Operational Baseline

- trusted Python path: `.venv312`
- trusted database path: `var/ov10.sqlite3`
- current fixture: `data/OV10_base_2025.xlsx`
- current repo-versioned portfolio config: `config/ov10_portfolio.toml`
- current governed quality toolchain: `ruff`, `pytest`, `pyright`, `eslint`, `markdownlint-cli2`, `yamllint`, `actionlint`, `shellcheck`, `PSScriptAnalyzer`, `sqlfluff`, `pip-audit`, `npm audit`, and `pre-commit`
- current repository sync audit path: `.codex/scripts/git_sync_audit.py` with optional Windows scheduling through `.codex/scripts/register_git_sync_audit_task.ps1`

## Current Goals

1. preserve the existing stronger OV10 architecture and documentation
2. adopt the useful parts of `final_kit` as a control plane under `.codex/`
3. keep autonomy grounded in real backlog items and validation evidence
4. continue toward deeper parity after the first workbook-config adapter for `config.carteiras` and `config.books`
5. keep the online/offline workbook compatibility boundary explicit in runtime-facing work
6. defer nonessential security hardening until after the planned functional MVP is cleanly delivered

## Current Limitations

- the first spreadsheet configuration adapter exists, but workbook parity is still partial
- the offline `.xlsx` reference is not an authoritative runtime equivalent of the online Google Sheets system
- synthetic workbook generation exists for the current ingestion contract, but scenario breadth is still intentionally small
- reconciliation is still import-focused, not yet full reference-output parity
- fiscal outputs now have first-pass contracts and coverage reporting, but not a full tax engine
- bulk `brapi` refresh is not reliable without a configured token even though the adapter is implemented
- valuation-aware reconciliation now depends on actual snapshot coverage in the selected database; an empty or stale database will correctly keep market fields as blockers
- dev-bridge and broader repo security hardening are intentionally deferred to a post-MVP phase unless the risk posture changes materially

## Current Risks

- the reference solution still contains logic split between workbook formulas and remotely loaded Apps Script code
- `repo_monitor.py` can trigger repeated `codex continue` runs when `HEAD` changes frequently
- long-running watchdog automation can create noisy activity unless the backlog and state files stay disciplined
- repository-loss risk rises quickly if checkpoint commits and pushes are skipped after validated workstreams

## Environment Baseline (2026-03-21)

- VS Code global baseline was normalized on 2026-03-21 for active work on `OV10` and `SGFD`
- PowerShell now resolves `code` through the VS Code CLI wrapper instead of `Code.exe`
- repo-tracked workspace files now exist under `.vscode/` and `.editorconfig`
- the intended OV10 interpreter for workspace execution is `.venv312`
- validation on 2026-04-05: `C:\git\OV10\.venv312\Scripts\python.exe -m pytest -q` passed with `39 passed`
- validation on 2026-04-05: `ruff check .` is green under the governed policy in `pyproject.toml`
- validation on 2026-04-05: `npm run typecheck:python` is green after adding valuation-aware market/FX reconciliation
- GitHub Actions CI now validates installability, `ruff`, `pytest`, `.codex/scripts` compilation, CLI help, governed type/schema/SQL checks, and dependency-audit commands
- the governed lint scope intentionally excludes legacy root-level scripts and `archive/`
- repository sync governance was added on 2026-03-21 after diagnosing a one-commit repo with a large active untracked surface; see `docs/diagnostics/2026-03-21_repository_sync_audit.md`
