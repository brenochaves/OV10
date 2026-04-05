# OV10 Setup And Operational Usage

Date: 2026-03-21

## Purpose

This document gives the current operational path to run the OV10 foundation safely on this machine.

## Python Environment

Current status:

- the global Python 3.13 installation is not reliable for project tooling
- a healthy isolated environment was created with Python 3.12 in `.venv312`
- Python 3.13 was partially recovered for missing `html.entities`, but its `pip`/tooling state is still inconsistent

Reason for using `.venv312`:

- `pytest`, `pip`, and packaging tooling work correctly there
- the project now runs independently from the broken global 3.13 setup

## Environment Commands

Create or refresh the environment:

```powershell
C:\Users\Breno\AppData\Local\Programs\Python\Python312\python.exe -m virtualenv -p C:\Users\Breno\AppData\Local\Programs\Python\Python312\python.exe .venv312
.\.venv312\Scripts\python.exe -m pip install -e .[dev]
npm install
```

Activate in PowerShell:

```powershell
.\.venv312\Scripts\Activate.ps1
```

Run without activation:

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
.\.venv312\Scripts\python.exe -m ruff check .
```

Install the governed `pre-commit` hook set:

```powershell
.\.venv312\Scripts\python.exe -m pre_commit install
```

Install the governed non-Python local tools on Windows:

```powershell
winget install --id rhysd.actionlint -e --accept-package-agreements --accept-source-agreements
winget install --id koalaman.shellcheck -e --accept-package-agreements --accept-source-agreements
pwsh -NoLogo -NoProfile -Command "Set-PSRepository PSGallery -InstallationPolicy Trusted; Install-Module PSScriptAnalyzer -Scope CurrentUser -Force -Repository PSGallery"
```

Recommended VS Code extensions for the governed toolchain:

- `charliermarsh.ruff`
- `ms-python.python`
- `dbaeumer.vscode-eslint`
- `davidanson.vscode-markdownlint`
- `redhat.vscode-yaml`
- `ms-vscode.powershell`
- `timonwong.shellcheck`

## Git Checkpoint Governance

Repository sync safety is governed separately from language lint and tests.

Primary policy:

- `docs/operations/GIT_CHECKPOINT_POLICY.md`

Direct audit command:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\git_sync_audit.py --fail-on warning
```

Write local audit artifacts under ignored `var\git_sync\`:

```powershell
pwsh -NoLogo -NoProfile -File .codex\scripts\run_git_sync_audit.ps1
```

Register a recurring Windows audit reminder task:

```powershell
pwsh -NoLogo -NoProfile -File .codex\scripts\register_git_sync_audit_task.ps1
```

Use the audit before long unattended runs and before ending a substantial work session.

## Current CLI Usage

Show ingestion summary for the current workbook:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli ingest-status-invest-xlsx data\OV10_base_2025.xlsx
```

Compute open positions from the current workbook:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli positions-from-xlsx data\OV10_base_2025.xlsx
```

Initialize the local database:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli init-db --database var\ov10.sqlite3
```

Persist the workbook into the governed SQLite store:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli persist-status-invest-xlsx data\OV10_base_2025.xlsx --database var\ov10.sqlite3 --config config\ov10_portfolio.toml
```

`--config` currently accepts:

- `.toml` repo-versioned config files
- `.xlsx` / `.xlsm` workbook config sources

When a workbook config source is used, OV10 imports the available `config.books` structure and falls back to the TOML portfolio baseline if `config.carteiras` is still a generic template.

Example using the checked-in reference workbook as config source:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli persist-status-invest-xlsx data\OV10_base_2025.xlsx --database var\ov10.sqlite3 --config "ov10_codex_handoff\Cópia de v6.4_Controle de Investimentos (Alpha).xlsx"
```

Inspect the persisted batch:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli batch-report status_invest_xlsx:eb06d84422c5 --database var\ov10.sqlite3
```

Inspect the governed instrument reference state for a batch:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli instrument-reference-report --database var\ov10.sqlite3 --batch-id status_invest_xlsx:eb06d84422c5
```

Refresh governed public market and FX snapshots:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli refresh-public-market-data --database var\ov10.sqlite3 --instrument-code PETR4 --fx-base-currency USD
```

For bulk `brapi` refresh, prefer an authenticated token:

```powershell
$env:OV10_BRAPI_TOKEN="your-token"
.\.venv312\Scripts\python.exe -m ov10.cli refresh-public-market-data --database var\ov10.sqlite3 --fx-base-currency USD
```

Inspect persisted market snapshots:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli market-snapshot-report --database var\ov10.sqlite3 --canonical-code PETR4
```

Inspect persisted FX snapshots:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli fx-snapshot-report --database var\ov10.sqlite3 --base-currency USD --quote-currency BRL
```

List persisted batches:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli list-batches --database var\ov10.sqlite3
```

Inspect broker/system cash balances for a batch:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli cash-balances status_invest_xlsx:eb06d84422c5 --database var\ov10.sqlite3
```

Inspect book-level positions for a batch:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli book-positions status_invest_xlsx:eb06d84422c5 --database var\ov10.sqlite3
```

Run the governed reconciliation harness against the checked-in reference workbook:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli reference-workbook-reconciliation data\OV10_base_2025.xlsx --reference-workbook "ov10_codex_handoff\Cópia de v6.4_Controle de Investimentos (Alpha).xlsx" --config config\ov10_portfolio.toml
```

Run the same harness with persisted market/FX consumption enabled:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli reference-workbook-reconciliation data\OV10_base_2025.xlsx --reference-workbook "ov10_codex_handoff\Cópia de v6.4_Controle de Investimentos (Alpha).xlsx" --config config\ov10_portfolio.toml --database var\ov10.sqlite3
```

Inspect the first governed DARF/DIRPF contract report:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli fiscal-contract-report data\OV10_base_2025.xlsx
```

Generate one synthetic workbook for a named scenario:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli generate-synthetic-status-invest-xlsx var\synthetic\base.xlsx --scenario base
```

Generate the full synthetic scenario matrix:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli generate-synthetic-status-invest-matrix var\synthetic
```

The persisted flow stores:

- canonical facts
- repo-versioned portfolio/book config
- source lineage per row
- observed instrument mappings
- governed instrument references
- governed market snapshots
- governed FX snapshots
- derived broker/system accounts
- derived cash movements and cash balances
- account-level position snapshots
- portfolio/book assignments
- book-level position snapshots
- position snapshots for `average_cost_v1`
- reconciliation output tied to the batch
- either repo-versioned TOML config or workbook-derived config normalization, depending on `--config`
- synthetic scenario workbooks can be generated locally to exercise the same ingestion path without real data

## Expected Reconciliation Output For Current Fixture

For `data\OV10_base_2025.xlsx`, the current reconciliation is expected to persist:

- `1` configured portfolio
- `5` configured books
- `1025` transactions
- `1486` dividend receipts
- `5` corporate actions
- `7` observed accounts
- `7` account-to-portfolio assignments
- `160` observed instrument mappings
- `2493` cash movements
- `7` cash balance snapshots
- `21` account position snapshots
- `21` book position snapshots
- `21` open position snapshots
- `2` reconciliation warnings and `0` blocking errors

Current warnings are:

- `2` x `conversion_alignment_mismatch`

The conversion warnings indicate that two rows in `Conversoes_Mapeadas` do not line up exactly with the conversion quantities observed in `Operacoes`.

The earlier system-account warning was removed from the current fixture after broker attribution was improved for corporate action cash. The single cash-bearing event now lands in `INTER DTVM LTDA` through unique same-day conversion evidence.

When the checked-in reference workbook is used as `--config`, the current fixture still persists `21` book position snapshots, but `books_loaded` changes from `5` to `11` because the workbook book model is more granular than the conservative TOML baseline.

For the reference workbook reconciliation harness, the current fixture is expected to report:

- `1` area as `expected`: `rendimentos`
- `3` areas as `blocking`: `portfolio.`, `caixa`, `alocação`

Interpretation:

- `rendimentos` already has strong conceptual parity from canonical dividend receipts
- `portfolio.` and `alocação` now consume persisted market/FX snapshots when `--database` is provided; remaining blockers depend on actual local snapshot coverage plus still-missing workbook concepts
- `caixa` is primarily blocked by missing manual cash classes such as initial balance, remittance/withdrawal, and credit/debit

Operator note for market-aware reconciliation:

1. persist the fixture or batch into SQLite
2. refresh governed market/FX snapshots into the same database
3. run `reference-workbook-reconciliation --database ...`

If the database has no persisted market coverage for the open positions, the
report will correctly keep those workbook fields as `blocking`.

## Market Snapshot Notes

The first governed market adapter currently supports only Brazil-listed first-pass types:

- `stock_br`
- `fii`
- `bdr`
- `etf_br`

Operational note from the real fixture on 2026-03-21:

- a tokenless single-instrument `brapi` refresh succeeded for `PETR4`
- bulk tokenless refresh over the eligible surface did not succeed reliably
- `OV10_BRAPI_TOKEN` or `--brapi-token` is therefore the recommended operator path for broad refreshes
- the official BCB PTAX adapter succeeded for `USD/BRL`

## Validation Commands

Run tests:

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
```

Run lint:

```powershell
.\.venv312\Scripts\python.exe -m ruff check .
```

Check formatting:

```powershell
.\.venv312\Scripts\python.exe -m ruff format . --check
```

Governed lint scope note:

- `ruff check .` is the supported lint gate for the current OV10 surface
- legacy exploratory root scripts and `archive/` are intentionally excluded by policy
- if one of those files is promoted into active OV10 runtime use, it should be brought back under the lint gate

Validate the `.codex` helper scripts compile:

```powershell
.\.venv312\Scripts\python.exe -m compileall .codex\scripts
```

Validate repository sync posture:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\git_sync_audit.py --fail-on warning
```

Validate Apps Script lint:

```powershell
npm run lint:apps-script
```

Validate Python type checking:

```powershell
npm run typecheck:python
```

Validate active Markdown:

```powershell
npm run lint:markdown
```

Validate governed YAML:

```powershell
.\.venv312\Scripts\python.exe -m yamllint .github\workflows\ci.yml .codex\SYSTEM_STATE.yaml
```

Validate GitHub Actions semantics:

```powershell
& (Get-ChildItem $env:LOCALAPPDATA\Microsoft\WinGet\Packages -Recurse -Filter actionlint.exe | Select-Object -First 1 -ExpandProperty FullName)
```

Validate the Unix watchdog shell script:

```powershell
& (Get-ChildItem $env:LOCALAPPDATA\Microsoft\WinGet\Packages -Recurse -Filter shellcheck.exe | Select-Object -First 1 -ExpandProperty FullName) .codex/scripts/watchdog_loop.sh
```

Validate the PowerShell watchdog script:

```powershell
pwsh -NoLogo -NoProfile -Command "Invoke-ScriptAnalyzer -Path '.codex/scripts/*.ps1' -Settings 'PSScriptAnalyzerSettings.psd1' -EnableExit"
```

Validate governed SQL:

```powershell
.\.venv312\Scripts\python.exe -m sqlfluff lint sql
```

Audit Python dependencies:

```powershell
.\.venv312\Scripts\python.exe -m pip_audit --progress-spinner off --skip-editable
```

Audit Node dependencies:

```powershell
npm run audit:node
```

Smoke-check the CLI entry point:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli --help
```

## CI

The repository now includes GitHub Actions validation in:

- `.github/workflows/ci.yml`

The workflow uses Python `3.12` and runs the same governed checks as the operator path:

- `python -m pip install -e .[dev]`
- `npm ci`
- `python -m ruff check .`
- `python -m ruff format . --check`
- `python -m pytest -q`
- `npm run typecheck:python`
- `python -m yamllint .github/workflows/ci.yml .codex/SYSTEM_STATE.yaml`
- `actionlint`
- `npm run lint:apps-script`
- `npm run lint:markdown`
- `shellcheck .codex/scripts/watchdog_loop.sh`
- `Invoke-ScriptAnalyzer -Path '.codex/scripts/*.ps1' -Settings 'PSScriptAnalyzerSettings.psd1' -EnableExit`
- `python -m sqlfluff lint sql`
- `python -m pip_audit --progress-spinner off --skip-editable`
- `npm run audit:node`
- `python -m compileall .codex/scripts`
- `python -m ov10.cli --help`

## Pre-commit

The repo now exposes a governed local hook orchestrator in:

- `.pre-commit-config.yaml`

Install once:

```powershell
.\.venv312\Scripts\python.exe -m pre_commit install
```

Run manually across the whole active surface:

```powershell
.\.venv312\Scripts\python.exe -m pre_commit run --all-files
```

Implementation note:

- the hook config does not define a second quality policy
- it delegates to `.codex/scripts/run_precommit_checks.py`
- that script runs the same governed local commands already documented above

## Online Runtime Bridge

The repo now includes an online-first Apps Script bridge under:

- `apps_script_debug_bridge/`

Purpose:

- inspect the live Google Sheets reference workbook
- derive the runtime script version from `LeiaMe!B6`
- capture the remote JavaScript payload loaded by the original `_Utils.js`
- create a debug copy before any bound-script instrumentation

Working directory:

```powershell
Set-Location C:\git\OV10\apps_script_debug_bridge
```

Push bridge code:

```powershell
cmd /c clasp push -f
```

Create a versioned deployment:

```powershell
cmd /c clasp version "OV10 debug bridge"
cmd /c clasp deploy -d "OV10 Debug Bridge"
```

Open the bridge project in the browser:

```powershell
cmd /c clasp open
```

Likely one-time authorization flow:

- run `dbgPing` from the Apps Script editor
- approve the requested Google scopes
- if Google shows the unverified-app interstitial, use `Advanced` and continue to the project because this is your own debug bridge

Important note:

- the bridge is currently operated through the deployed web app, not through `clasp run`
- web access was relaxed and is now gated by an explicit `bridgeKey`
- the current trusted runtime wrapper in OV10 already injects the correct `bridgeKey`
- `clasp run` can still be unreliable for this project even after browser authorization

Primary bridge functions:

- `dbgPing`
- `dbgListSheets`
- `dbgReadRange`
- `dbgSheetPreview`
- `dbgWorkbookVersion`
- `dbgFetchRemoteScriptSummary`
- `dbgFetchRemoteScriptChunk`
- `dbgCreateDebugCopy`
- `dbgDescribeProtections`

Use this bridge for online runtime investigation. Do not use the offline `.xlsx` export as proof of live execution behavior.

## Online Runtime Capture CLI

OV10 now has Python wrappers around the Apps Script bridge for reproducible capture.

Create another debug copy of the online workbook:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli create-online-debug-copy
```

Capture the remotely loaded script payload to local artifacts:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli capture-online-remote-script var\online_runtime\reference
```

Current validated output:

- payload path: `var\online_runtime\reference\v61_controle_64.js`
- metadata path: `var\online_runtime\reference\v61_controle_64.metadata.json`
- catalog path: `var\online_runtime\reference\v61_controle_64.catalog.json`

Generate a classified function catalog from the captured payload:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli analyze-online-remote-script var\online_runtime\reference\v61_controle_64.js
```

These artifacts are intentionally written under `var/` and are not committed by default.

## `.codex` Control Plane Usage

The repo now includes a selective autonomy control plane under `.codex/`.

Primary files:

- `.codex/CONTEXT.md`
- `.codex/BACKLOG.md`
- `.codex/TASK_GRAPH.md`
- `.codex/DECISIONS.md`
- `.codex/PROJECT_MEMORY_INDEX.md`
- `.codex/ARCHITECTURE_MAP.md`
- `.codex/REPOSITORY_KNOWLEDGE_GRAPH.md`
- `.codex/INTEGRATION_REPORT.md`

Important rule:

- `.codex/` does not override `src/ov10/`, `tests/`, `docs/adr/`, `docs/diagnostics/`, or this runbook

Refresh the context snapshot:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\context_rotator.py
```

Append a backlog task template:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\generate_task_template.py
```

Review heuristic backlog priority hints:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\task_priority_engine.py
```

## Continuous Automation Scripts

The kit-style continuous automation is available but intentionally opt-in.

Repo monitor:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\repo_monitor.py
```

Environment variables:

- `POLL_SECONDS`
- `CODEX_CONTINUE_COMMAND`

Risk note:

- `repo_monitor.py` triggers `codex continue` whenever `git rev-parse HEAD` changes
- this can create repeated or noisy autonomous runs if commits, rebases, or external git updates happen frequently
- use it only when that behavior is desired

Windows watchdog loop in PowerShell:

```powershell
$env:INTERVAL_SECONDS = 300
.\.codex\scripts\watchdog_loop.ps1
```

Windows watchdog loop in batch:

```powershell
set INTERVAL_SECONDS=300
.codex\scripts\watchdog_loop.bat
```

Unix watchdog loop:

```powershell
bash .codex/scripts/watchdog_loop.sh
```

Behavior:

- all watchdog variants repeatedly run `codex continue`
- failures are ignored so the loop keeps running
- use them only when the current backlog and state files are trustworthy enough for unattended continuation
- run the Git sync audit first; unattended continuation with a risky dirty worktree defeats the checkpoint policy

## Current Known Limitations

- the new OV10 core is still foundation-level
- SQLite is the current local-first persistence layer; PostgreSQL is still a later target
- reconciliation exists but is still basic and focused on import-quality checks
- broker-level cash ledger and a first repo-versioned portfolio/book config now exist
- a governed reference workbook reconciliation harness now exists, but it is still selective and not a full live Google Sheets parity engine
- the first fiscal layer now exists only as contract and coverage reporting; DARF/DIRPF calculations are still intentionally partial
- allocation is still conservative and based on instrument-type routing, not yet on a full spreadsheet-config import
- synthetic scenario generation currently targets the Status Invest style ingestion workbook, not the full reference workbook surface
- `.codex` automation is available, but the repo monitor and watchdog loops are intentionally operator-controlled because they can produce noisy autonomous runs
- tax and broader reporting layers are not implemented yet
- the legacy root-level Python scripts remain exploratory and should not be treated as the production core
- the global Python 3.13 installation still appears incomplete and should not be used for this repo until repaired
