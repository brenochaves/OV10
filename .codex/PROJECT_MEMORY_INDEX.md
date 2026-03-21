# PROJECT MEMORY INDEX

## Product / repository identity

- `project_name`: OV10
- `primary_goal`: build a governed personal portfolio accounting core with reproducible ingestion, persistence, cash, positions, allocation, and later fiscal outputs
- `key_users_or_consumers`: current repository operator and future end users consuming OV10 through CLI, storage, and downstream interfaces

## Stack summary

- `languages`: Python 3.12, JavaScript / Apps Script, PowerShell, shell, YAML, JSON, TOML, SQL, Markdown
- `frameworks`: standard library CLI, pandas, openpyxl, governed `.codex` control plane
- `package_managers`: `pip` through `pyproject.toml`, `npm` through `package.json`
- `databases`: SQLite local-first
- `test_tooling`: pytest, unittest-compatible tests, ruff, pyright, sqlfluff, eslint, markdownlint-cli2, yamllint, actionlint, shellcheck, PSScriptAnalyzer, pip-audit, npm audit, pre-commit
- `synthetic_test_inputs`: local `.xlsx` scenario generator under `src/ov10/testing/`
- `ci_cd`: GitHub Actions validation in `.github/workflows/ci.yml`

## Operational constraints

- `release_cadence`: active local development, no packaged release cycle yet
- `security_sensitivity`: moderate, because portfolio and tax-adjacent data are financially sensitive
- `external_credentials_or_integrations`: local workbook inputs, Google Apps Script reverse engineering artifacts, external market and event research sources
- `uptime_or_performance_sensitivity`: low for current local-first workflow, but reproducibility and auditability are high priority

## Conventions already materialized in code

- `naming`: snake_case for Python modules and identifiers; explicit version suffixes for engines such as `average_cost_v1`
- `layering`: `ingestion -> domain -> positions/cash/config/allocation -> services -> storage -> cli`
- `module_boundaries`: source adapters stay in `ingestion/`, persistence in `storage/`, orchestration in `services/`, user entry points in `cli.py`
- `api_conventions`: CLI returns JSON payloads; storage operations are batch-oriented and keyed by deterministic identifiers
- `configuration_conventions`: portfolio config can come from governed TOML or normalized workbook config, with TOML fallback when workbook portfolio data is still template-level
- `migration_patterns`: structural changes should land with ADRs; new governed behavior belongs under `src/ov10/`, not the legacy root scripts
- `logging_or_observability_patterns`: current observability is mostly via JSON CLI output, reconciliation warnings, lineage tables, and versioned documentation
- `repository_governance_patterns`: Git checkpoint policy in `docs/operations/GIT_CHECKPOINT_POLICY.md`, local sync audit under `.codex/scripts/git_sync_audit.py`, and scheduled Windows reminder support

## Trusted Sources Inside The Repo

- `highest_trust_code`: `src/ov10/`
- `highest_trust_validation`: `tests/`
- `highest_trust_decisions`: `docs/adr/`
- `highest_trust_research`: `docs/diagnostics/`
- `highest_trust_operations`: `docs/operations/`
- `control_plane`: `.codex/`

## Known Environment Facts

- `.venv312` is the trusted Python environment for the repo
- the global Python 3.13 installation remains unsuitable as the primary project environment
- the default local database path is `var/ov10.sqlite3`
- the current reference fixture is `data/OV10_base_2025.xlsx`
- repository sync hygiene is now part of the active control plane and must be kept visible during long autonomous runs
