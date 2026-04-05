# ADR 0020: Persisted Market/FX Consumption In Reconciliation

Date: 2026-04-05

## Status

Accepted

## Context

OV10 already had:

- canonical `market_snapshot` and `fx_snapshot` contracts
- provider adapters for `brapi` and BCB PTAX
- persistence and CLI inspection paths for both layers
- a governed reference workbook reconciliation harness

However, the reconciliation harness still treated market-driven fields in
`portfolio.` and `alocação` as placeholder blockers even when persisted market
coverage could exist.

That left a structural gap:

- the storage layer could persist valuation inputs
- the report layer could not consume them
- parity statements could not distinguish between:
  - missing valuation logic
  - missing provider coverage in the local database

## Decision

OV10 now consumes the latest persisted `market_snapshot` and `fx_snapshot`
records inside the reference workbook reconciliation path.

Implementation rules:

1. Reconciliation remains deterministic by default.
   - `reference-workbook-reconciliation` only consumes persisted market/FX
     layers when `--database` is explicitly provided.
   - Database-free execution remains the structural baseline.

2. Valuation is derived from persisted facts, not from provider calls at report
   time.
   - latest market snapshots are resolved by `canonical_code`
   - latest FX snapshots are resolved by currency pair
   - both are bounded by the current snapshot date when available

3. Coverage classification is now evidence-based.
   - full coverage marks the relevant workbook fields as `expected`
   - partial coverage marks them as `explained`
   - zero coverage keeps them `blocking`

4. The report distinguishes valuation logic from provider coverage.
   - if market/FX rows are absent from the database, blockers remain visible
   - if persisted rows exist, the report consumes them without changing the
     ingestion or position engine contracts

## Consequences

Positive:

- `portfolio.` can now consume persisted `market_cod`, `nome_pregao`, `price`,
  `change`, `changepct`, `moeda_price`, and `pm_fx`
- `alocação` can now consume persisted `VALOR DE MERCADO`, `LUCRO TOTAL`, and
  `%`
- parity reporting becomes more honest about whether the blocker is data
  coverage or missing logic
- the valuation layer remains additive and reversible

Trade-offs:

- operator flow is now two-stage for market parity:
  1. persist the batch
  2. refresh market/FX snapshots
  3. run reconciliation with `--database`
- a stale or empty local database will still show market blockers

## Validation

- `tests/test_market_valuation.py`
- `tests/test_reference_workbook_reconciliation.py`
- `python -m pytest -q` -> `39 passed`
- `npm run typecheck:python` -> `0 errors`
