# DECISIONS

Canonical structural decisions live in `docs/adr/`. This file is a concise operational index, not a replacement for ADRs.

### 2026-03-12 09:00 - Establish `src/ov10` as the governed implementation path
Decision:
Use `src/ov10/` as the new domain core and keep root-level Python scripts as exploratory artifacts only.
Context:
The repository started with exploratory scripts and spreadsheets but no package structure or governed evolution path.
Chosen option:
Adopt ADR 0001 and build all new core behavior under `src/ov10/`.
Why:
This creates a clean migration path without destructive rewrites of user artifacts.
Evidence:
`docs/adr/0001-domain-foundation.md`

### 2026-03-12 10:00 - Start with a Status Invest style XLSX adapter and canonical batch lineage
Decision:
Prioritize a governed adapter for the current workbook and persist idempotent import batches with row-level lineage.
Context:
The current user-available source is an XLSX export style workbook, not a clean API contract.
Chosen option:
Adopt ADRs 0002, 0003, and 0004 as the ingestion and persistence foundation.
Why:
Canonical ingestion is required before positions, cash, or reconciliation can be trusted.
Evidence:
`docs/adr/0002-status-invest-xlsx-first-adapter.md`
`docs/adr/0003-sqlite-persistence-and-reconciliation.md`
`docs/adr/0004-observed-instrument-mapping-seed.md`

### 2026-03-12 11:00 - Derive cash and account context instead of hiding incomplete broker attribution
Decision:
Persist derived accounts, cash movements, and balance snapshots, including a visible system account when attribution is missing.
Context:
Corporate action cash components can arrive without broker attribution in the current source data.
Chosen option:
Adopt ADR 0005 and keep the mismatch visible in reconciliation output.
Why:
Visibility is preferable to silent misallocation.
Evidence:
`docs/adr/0005-derived-cash-ledger-and-account-registry.md`

### 2026-03-12 12:00 - Use a repo-versioned portfolio and book configuration baseline
Decision:
Represent portfolio and book routing in a TOML file until the spreadsheet-config adapter exists.
Context:
The reference workbook has a rich config layer, but the current adapter does not carry that configuration.
Chosen option:
Adopt ADR 0006 and use `config/ov10_portfolio.toml` as the current source of truth for allocation.
Why:
This keeps allocation governed and reviewable instead of implicit.
Evidence:
`docs/adr/0006-repo-versioned-portfolio-book-config.md`

### 2026-03-12 14:45 - Adopt `final_kit` selectively as an OV10 control plane
Decision:
Bring `final_kit` concepts into `.codex/`, but preserve OV10 code, tests, ADRs, diagnostics, and operator docs as higher-trust sources.
Context:
`final_kit` contributes autonomy scaffolding, backlog and memory structures, prompts, and scripts, but it is generic and partially broken.
Chosen option:
Adapt the useful parts, rewrite broken pieces, and document the operator-managed risk of continuous monitors.
Why:
The repo benefits from durable autonomy state without downgrading already stronger OV10 assets.
Evidence:
`docs/adr/0007-selective-codex-control-plane-adoption.md`
`.codex/INTEGRATION_REPORT.md`

### 2026-03-12 16:30 - Add a first workbook-based config adapter with governed fallback
Decision:
Allow portfolio and book config loading from `.xlsx` or `.xlsm`, normalizing workbook books into current contracts and falling back to the TOML portfolio baseline when workbook portfolios are still generic.
Context:
The reference workbook carries high-value configuration structure, but the current checked-in artifact is template-like in `config.carteiras` and richer in `config.books` than the current engine can fully express.
Chosen option:
Adopt ADR 0008 and keep unsupported workbook books imported but inactive, with an active `Sem Book` fallback.
Why:
This reuses real workbook structure now without pretending the current engine already supports every spreadsheet-level routing concept.
Evidence:
`docs/adr/0008-workbook-config-adapter-with-toml-fallback.md`

### 2026-03-12 18:00 - Add local synthetic workbook generation as the first scenario-testing backbone
Decision:
Generate fictitious workbook inputs locally in Python instead of making Apps Script or Google Sheets the primary testing harness.
Context:
OV10 needs scenario perturbation and edge-case coverage without depending on real user data.
Chosen option:
Adopt ADR 0009 and expose local synthetic scenario generation through `src/ov10/testing/` and the CLI.
Why:
Local generation is deterministic, versionable, testable, and CI-friendly.
Evidence:
`docs/adr/0009-local-synthetic-workbook-generation.md`
`src/ov10/testing/synthetic_status_invest.py`

### 2026-03-21 17:30 - Add repository checkpoint and sync governance
Decision:
Treat long-lived dirty worktrees and large untracked active surfaces as repository-governance failures, with explicit audit tooling and a scheduled local reminder path.
Context:
The repo had only one historical commit and the governed OV10 implementation had accumulated almost entirely outside Git.
Chosen option:
Adopt ADR 0019, add a Git checkpoint policy, add `.codex/scripts/git_sync_audit.py`, and wire repository hygiene into the active control plane.
Why:
Quality gates do not protect against machine loss if validated work is never committed or pushed.
Evidence:
`docs/adr/0019-repository-checkpoint-and-sync-governance.md`
`docs/diagnostics/2026-03-21_repository_sync_audit.md`
`docs/operations/GIT_CHECKPOINT_POLICY.md`
