# Market/FX Valuation Reconciliation

Date: 2026-04-05

## Goal

Close `TASK-113` by consuming governed `market_snapshot` and `fx_snapshot`
layers inside the reference workbook reconciliation harness.

## What Changed

Code paths added or updated:

- `src/ov10/reconciliation/market_valuation.py`
- `src/ov10/reconciliation/reference_workbook.py`
- `src/ov10/storage/sqlite.py`
- `src/ov10/cli.py`
- `tests/test_market_valuation.py`
- `tests/test_reference_workbook_reconciliation.py`

Main behavior:

- latest persisted market snapshots are now resolved by `canonical_code`
- latest persisted FX snapshots are now resolved by currency pair
- valuation is translated into the base currency before reconciliation
- `portfolio.` and `alocação` now classify market-driven fields by real
  coverage instead of static placeholder blockers

## Resulting Coverage Model

The harness now treats these `portfolio.` fields as coverage-driven:

- `market_cod`
- `nome_pregao`
- `pm_fx`
- `price`
- `change`
- `changepct`
- `moeda_price`

The harness now treats these `alocação` fields as coverage-driven:

- `%`
- `VALOR DE MERCADO`
- `LUCRO TOTAL`

Classification rules:

- full persisted coverage -> `expected`
- partial persisted coverage -> `explained`
- no persisted coverage -> `blocking`

## Validation Evidence

Targeted and full validation:

- `python -m pytest -q tests/test_market_valuation.py tests/test_reference_workbook_reconciliation.py tests/test_market_data.py`
- `python -m pytest -q` -> `39 passed`
- `python -m ruff check .` -> green
- `npm run typecheck:python` -> `0 errors`

New deterministic test evidence:

- a temp SQLite database is seeded with the checked-in fixture plus synthetic
  market snapshots for every open position
- when `--database` is provided, `portfolio.` reduces market blockers and
  promotes:
  - `market_cod`
  - `nome_pregao`
  - `price`
  - `pm_fx`
  - `moeda_price`
- `alocação` reduces blockers and promotes:
  - `VALOR DE MERCADO`
  - `LUCRO TOTAL`
  - `%`

## Real Local Database Observation

Command:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli reference-workbook-reconciliation --database var/ov10.sqlite3
```

Observed on the current local database:

- `positions_with_market_price`: `0`
- `positions_with_display_name`: `0`
- `positions_with_market_code`: `0`
- `valued_book_count`: `0`
- `books_with_profit_total`: `0`
- `books_with_current_weight`: `0`

Interpretation:

- the valuation/reconciliation layer is now wired correctly
- the current local database still lacks persisted market coverage for the open
  positions in the checked-in fixture
- remaining blockers in the real local run are therefore provider/data coverage
  blockers, not missing valuation-consumption logic

## Conclusion

`TASK-113` is satisfied.

The remaining market parity work is no longer “join the snapshot layer”; it is:

- improve persisted snapshot coverage for the instruments actually open in the
  fixture
- extend market metadata/reference coverage
- keep separating provider coverage limitations from missing accounting logic
