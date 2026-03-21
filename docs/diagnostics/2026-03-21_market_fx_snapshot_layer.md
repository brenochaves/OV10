# 2026-03-21 Market and FX Snapshot Layer

## Scope

This diagnostic records the first governed implementation of the temporal market layer that sits on top of `instrument_reference`.

It covers:

- snapshot contracts
- provider adapters
- persistence and CLI inspection
- real execution evidence against the current fixture and current public endpoints

## Implemented Surface

Code paths:

- `src/ov10/market/models.py`
- `src/ov10/market/providers.py`
- `src/ov10/market/services.py`
- `src/ov10/storage/sqlite.py`
- `src/ov10/cli.py`

New persisted tables:

- `market_snapshot`
- `fx_snapshot`

New CLI paths:

- `refresh-public-market-data`
- `market-snapshot-report`
- `fx-snapshot-report`

## First-Pass Support Boundary

The first governed `brapi` adapter selects only:

- `stock_br`
- `fii`
- `bdr`
- `etf_br`

with base currency `BRL`.

From the current `instrument_reference` state in `var/ov10.sqlite3` on 2026-03-21:

- total active canonical references: `160`
- first-pass `brapi`-eligible references: `120`
- structurally out of scope for this pass: `40`

Breakdown by instrument type observed in the fixture:

- `stock_br`: `88`
- `fii`: `27`
- `bdr`: `3`
- `etf_br`: `2`
- `stock_us`: `22`
- `etf_us`: `9`
- `crypto`: `4`
- `treasury_br`: `4`
- `fund_br`: `1`

## Real Provider Evidence

### PTAX

Command:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli refresh-public-market-data --database var\ov10.sqlite3 --fx-base-currency USD
```

Observed result:

- `USD/BRL` snapshot persisted successfully
- selected bulletin date: `2026-03-20`
- bulletin type: `Fechamento`
- bid: `5.2793`
- ask: `5.28`
- canonical midpoint rate: `5.27965`

Inspection path:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli fx-snapshot-report --database var\ov10.sqlite3 --base-currency USD --quote-currency BRL
```

### Brapi

Single-instrument tokenless run succeeded:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli refresh-public-market-data --database var\ov10.sqlite3 --instrument-code PETR4 --fx-base-currency USD
```

Observed persisted market snapshot:

- `PETR4`
- provider: `brapi`
- snapshot date: `2026-03-20`
- price: `45.67`

Inspection path:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli market-snapshot-report --database var\ov10.sqlite3 --canonical-code PETR4
```

Bulk tokenless run over the whole first-pass eligible surface did **not** succeed operationally on 2026-03-21:

- selected instruments: `120`
- persisted market snapshots: `0`
- provider failures classified explicitly as `provider_request_failed`

Interpretation:

- the adapter itself is functional
- `brapi` is not reliable for bulk unauthenticated refresh in this environment
- operator token support is therefore part of the governed path, not an optional afterthought

## Design Consequences

The main repository blocker has now changed.

OV10 no longer lacks a market/FX snapshot contract or persistence surface. The remaining gap is consumption:

- join latest `market_snapshot` into valuation logic
- join latest `fx_snapshot` into valuation and cash translation logic
- reduce `portfolio.` and `alocação` blockers in the reconciliation harness with real persisted values

## Current Risks

- first-pass coverage is intentionally partial by instrument type
- broad `brapi` refreshes need configured authentication for predictable operation
- source-specific symbol mapping beyond canonical code passthrough is not yet implemented

## Recommended Next Step

Create the next governed task to consume latest market and FX snapshots inside valuation/reconciliation, instead of leaving those fields as explicit gaps.
