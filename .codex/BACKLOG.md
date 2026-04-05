# BACKLOG

## TASK-101
status: DONE
priority: P0
type: config_adapter
summary: Import `config.carteiras` and `config.books` from the reference workbook into the current OV10 portfolio and book contracts.
acceptance:
- a governed adapter reads the relevant workbook tabs into current config contracts
- current TOML loading remains supported as a fallback or override path
- at least one fixture-backed test validates the imported routing behavior
- an ADR documents source precedence and migration rules

dependencies: none
notes: Delivered on 2026-03-12 with workbook-book normalization, inactive unsupported books, and TOML fallback for template-like portfolio data.

## TASK-102
status: DONE
priority: P1
type: reconciliation
summary: Reduce or eliminate `system_cash_account_used` by improving broker attribution for corporate action cash components.
acceptance:
- current unmatched corporate action cash rows are classified explicitly
- known attribution rules are implemented or documented as unresolved
- reconciliation differentiates between expected and suspicious system-account usage
- tests cover at least one attributed and one unattributed scenario

dependencies: TASK-101
notes: Delivered on 2026-03-12 with a governed attribution heuristic backed by captured runtime evidence. The current real fixture no longer uses the system account for corporate action cash, and unresolved paths are now classified explicitly as `ambiguous` or `no_candidate`.

## TASK-103
status: DONE
priority: P1
type: reconciliation
summary: Strengthen reconciliation against reference workbook outputs for positions, cash, and allocation.
acceptance:
- at least one comparison harness exists for selected reference tabs
- divergences are classified as expected, explained, or blocking
- validation is reproducible from the checked-in fixture and config

dependencies: TASK-101
notes: Delivered on 2026-03-19 with the `reference-workbook-reconciliation` CLI and a governed comparison harness covering `portfolio.`, `caixa`, `alocação`, and `rendimentos`. The current checked-in fixture closes `rendimentos` as `expected` and leaves the other three areas explicitly `blocking`, with gaps classified as expected, explained, or blocking.

## TASK-104
status: DONE
priority: P1
type: market_reference
summary: Build the first governed market and instrument reference layer from workbook evidence and observed mappings.
acceptance:
- current observed mappings are normalized into a durable reference model
- instrument identity rules are documented
- at least one CLI or report path exposes the normalized mapping state

dependencies: TASK-101
notes: Delivered on 2026-03-19 with the new `instrument_reference` canonical table, normalized identity rules documented in ADR 0014, and the `instrument-reference-report` CLI exposing aliases plus observation counts. Market/FX valuation data is still a separate follow-up task.

## TASK-112
status: DONE
priority: P1
type: market_snapshot
summary: Add governed market and FX snapshot contracts with provider adapters for public sources.
acceptance:
- canonical contracts exist for market price and FX snapshots
- at least one public provider adapter is implemented for Brazil-listed assets
- at least one official FX adapter is implemented
- the persisted snapshot layer is inspectable by CLI or report

dependencies: TASK-104
notes: Delivered on 2026-03-21 with canonical `market_snapshot` and `fx_snapshot` tables, a governed `brapi` quote adapter, a governed BCB PTAX adapter, separate refresh/report CLI paths, and explicit first-pass coverage classification. Bulk `brapi` refresh now supports optional bearer token through `--brapi-token` / `OV10_BRAPI_TOKEN`.

## TASK-113
status: DONE
priority: P1
type: valuation_reconciliation
summary: Consume governed market and FX snapshots to reduce `portfolio.` and `alocação` blockers.
acceptance:
- latest persisted market snapshots can be joined to current position snapshots
- latest persisted FX snapshots can be joined where valuation or translation requires them
- the reference workbook reconciliation harness replaces placeholder market/FX gaps with real persisted values when coverage exists
- remaining parity gaps distinguish valuation logic from provider coverage limitations

dependencies: TASK-103, TASK-112
notes: Delivered on 2026-04-05 with an explicit market-valuation layer, latest-snapshot lookup helpers in SQLite, and reference-workbook reconciliation that degrades market-driven fields by real persisted coverage. Database-free runs remain deterministic; `--database` enables valuation-aware parity checks.

## TASK-114
status: DONE
priority: P2
type: quality_governance
summary: Add governed multi-stack static analysis for the active OV10 repository surface.
acceptance:
- active Apps Script, Markdown, YAML, shell, and PowerShell surfaces have explicit static-analysis gates
- local operator setup documents the required tools and commands
- CI runs the same governed static-analysis commands as the operator path
- VS Code recommendations align with the governed toolchain

dependencies: TASK-106
notes: Delivered on 2026-03-21 with ESLint for Apps Script, markdownlint-cli2 for active documentation, YamlLint plus Actionlint for workflow/config YAML, ShellCheck for the Unix watchdog, and PSScriptAnalyzer for the PowerShell watchdog. The governed scope remains intentionally narrower than full repo-wide linting for archived and legacy material.

## TASK-105
status: DONE
priority: P2
type: fiscal
summary: Define canonical contracts for tax outputs aligned with `darf` and `dirpf`.
acceptance:
- domain models for the first fiscal outputs exist
- scope boundaries between accounting and tax layers are documented
- backlog follow-ups identify missing source data and rule dependencies

dependencies: TASK-103
notes: Delivered on 2026-04-05 with an explicit fiscal module, workbook-aligned DARF/DIRPF contracts, a `fiscal-contract-report` CLI, and declared dependency gaps for tax lots, fiscal code mapping, prior-year snapshots, and manual fiscal inputs. Full tax calculation remains intentionally out of scope for this first pass.

## TASK-106
status: DONE
priority: P2
type: automation
summary: Add CI validation for pytest, ruff, and package installability using the trusted Python baseline.
acceptance:
- repo automation runs the documented quality gates
- failures are visible before manual release or handoff
- the CI spec references the same commands as `docs/operations/SETUP_AND_USAGE.md`

dependencies: none
notes: Delivered on 2026-03-21 with `.github/workflows/ci.yml`, Python 3.12 validation on GitHub Actions, editable install with `.[dev]`, governed `ruff check .`, `pytest -q`, `.codex/scripts` compile validation, and a CLI smoke check.

## TASK-107
status: TODO
priority: P3
type: docs
summary: Expand operator documentation for batch lifecycle, database inspection, and controlled use of `.codex` automation.
acceptance:
- runbook covers normal workflow and monitor/watchdog safety notes
- operator commands are grounded in checked-in scripts and current CLI behavior
- documentation avoids speculative future UI or API promises

dependencies: none
notes: Documentation should stay close to implemented behavior.

## TASK-115
status: TODO
priority: P3
type: security_hardening
summary: Harden the development bridge and broader repository security posture after the functional MVP and planned backlog are complete.
acceptance:
- bridge secret handling is reviewed and moved away from hardcoded development defaults if still justified
- bridge access posture is re-evaluated against the then-current operator workflow and automation requirements
- at least one governed secret-scanning path exists for the active repository surface
- SCA and other security gates are reviewed for promotion from informational to enforced where the cost is justified

dependencies: TASK-113, TASK-105
notes: Explicitly deferred on 2026-03-21 by operator decision. The current development priority is functional delivery and clean MVP execution, not hardening the dev bridge or broader security posture. Revisit once the planned functional backlog is materially complete.

## TASK-116
status: DONE
priority: P2
type: type_checking
summary: Add governed Python type checking for the active OV10 surface.
acceptance:
- `pyright` or equivalent is configured for `src/ov10`
- local operator docs include the type-check command
- CI includes the same governed type-check command
- initial scope and exclusions are documented explicitly

dependencies: TASK-114
notes: Delivered on 2026-03-21 with `pyright` scoped to `src/ov10`, aligned local docs, VS Code tasks, CI execution, and a green governed baseline.

## TASK-117
status: DONE
priority: P2
type: config_validation
summary: Add explicit governed validation for active TOML and structured JSON artifacts.
acceptance:
- active TOML config files have explicit schema or model validation
- structured JSON artifacts consumed by OV10 are validated before use where practical
- validation failures are actionable and operator-visible
- tests cover at least one invalid TOML case and one invalid JSON case

dependencies: TASK-114
notes: Delivered on 2026-03-21 with explicit TOML contract validation in `portfolio_books.py`, runtime bridge JSON response validation, market metadata JSON validation, and fixture-backed invalid-config tests.

## TASK-118
status: DONE
priority: P2
type: sql_static_analysis
summary: Add a governed SQL lint path for embedded SQLite SQL and future migration material.
acceptance:
- a SQL linter is configured with a deliberately narrow governed scope
- the chosen dialect matches the current SQLite baseline
- local docs and CI include the same SQL lint command
- current embedded SQL passes the first governed rule set

dependencies: TASK-114
notes: Delivered on 2026-03-21 by extracting the SQLite schema to `sql/schema.sql`, loading it from the runtime store, and governing it with `sqlfluff` under the SQLite dialect.

## TASK-119
status: DONE
priority: P2
type: sca
summary: Add governed software-composition analysis for Python and Node development dependencies.
acceptance:
- Python dependency auditing exists in a reproducible command path
- Node dependency auditing exists in a reproducible command path
- operator docs classify the initial mode as informational or enforced
- CI runs the chosen commands in the documented mode

dependencies: TASK-114
notes: Delivered on 2026-03-21 with reproducible `pip_audit --skip-editable` and `npm audit --audit-level=moderate` commands wired into docs and CI. The current baseline is green after upgrading `markdownlint-cli2`.

## TASK-120
status: DONE
priority: P3
type: local_automation
summary: Add a governed `pre-commit` orchestration layer for the active repository quality gates.
acceptance:
- pre-commit hooks invoke the governed local analysis commands
- the hook set stays aligned with operator docs and CI
- installation and bypass behavior are documented clearly

dependencies: TASK-116, TASK-117, TASK-118
notes: Delivered on 2026-03-21 with `.pre-commit-config.yaml` delegating to `.codex/scripts/run_precommit_checks.py`, keeping the local hook set aligned with the governed operator commands.

## TASK-121
status: DONE
priority: P1
type: repo_governance
summary: Add explicit Git checkpoint and remote-sync governance to prevent validated work from remaining outside version control.
acceptance:
- a repository policy documents checkpoint cadence and push expectations
- current repository-loss risk is captured in a diagnostic artifact
- the `.codex` control plane reflects repository hygiene as an active rule
- the governed path distinguishes tracked, ignored, and unacceptable unclassified work

dependencies: none
notes: Delivered on 2026-03-21 with ADR 0019, a repository-sync diagnostic, `docs/operations/GIT_CHECKPOINT_POLICY.md`, and control-plane rules covering checkpoint cadence and long-lived dirty worktrees.

## TASK-122
status: DONE
priority: P1
type: repo_automation
summary: Add local repository sync audit automation and a Windows scheduled reminder path.
acceptance:
- a local audit script reports tracked/untracked counts, dirty-state age, and upstream divergence
- operator docs include direct and scheduled audit commands
- VS Code exposes a task for the audit path
- audit artifacts can be written locally without polluting the governed repo surface

dependencies: TASK-121
notes: Delivered on 2026-03-21 with `.codex/scripts/git_sync_audit.py`, PowerShell wrappers for direct and scheduled execution, and local audit artifacts written under ignored `var/git_sync/`.

## TASK-108
status: DONE
priority: P2
type: synthetic_data
summary: Add governed synthetic workbook generation and perturbation scenarios for local testing.
acceptance:
- synthetic `.xlsx` generation exists for the current ingestion contract
- at least one scenario matrix can be produced locally
- automated tests exercise synthetic round-trip and edge-case behavior
- specialist ownership is documented

dependencies: none
notes: Delivered on 2026-03-12 under the local-first testing strategy documented in ADR 0009.

## TASK-109
status: TODO
priority: P1
type: compatibility_audit
summary: Establish an explicit compatibility boundary between the offline `.xlsx` export and the online Google Sheets + Apps Script runtime.
acceptance:
- the repo documents which workbook areas are structural references vs executable online-only behavior
- Google Sheets-specific formula degradation is quantified and classified by sheet
- the impact of Apps Script orchestration and remote-loaded code is tied to concrete risk statements
- downstream reconciliation work uses this boundary instead of assuming offline/runtime equivalence

dependencies: none
notes: Added after confirming heavy `__xludf.DUMMYFUNCTION`, `QUERY`, and `GOOGLEFINANCE` presence in the exported workbook.

## TASK-110
status: DONE
priority: P0
type: online_runtime_bridge
summary: Use a standalone Apps Script bridge to capture live workbook behavior and the remotely loaded script payload.
acceptance:
- a standalone bridge project is versioned in the repo
- bridge code can derive the workbook version, list sheets, create a debug copy, and fetch remote payload chunks
- deployment evidence is documented
- remaining authorization steps, if any, are explicit and narrow

dependencies: none
notes: Delivered on 2026-03-12 with bridge deployment, debug copy creation, and successful capture of `v61_controle_64`.

## TASK-111
status: DONE
priority: P0
type: runtime_analysis
summary: Classify the captured remote Apps Script payload into domain modules, workflows, and rule clusters that can be mapped into OV10 contracts.
acceptance:
- a first catalog of major function groups is produced from the captured payload
- high-value rule areas are identified, such as positions, dividends, portfolio allocation, DARF, DIRPF, and update flows
- low-value utility or UI sections are separated from core business logic
- findings are documented with concrete references into the captured artifact

dependencies: TASK-110
notes: Delivered on 2026-03-12 through a generated catalog of 483 unique functions, with domain-oriented grouping, high-value rule clusters, and concrete references documented in `docs/diagnostics/2026-03-12_remote_payload_function_catalog.md`.
