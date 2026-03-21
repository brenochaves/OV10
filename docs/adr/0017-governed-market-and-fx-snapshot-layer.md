# ADR 0017: Governed Market and FX Snapshot Layer

Date: 2026-03-21

## Status

Accepted

## Context

OV10 already had:

- canonical transaction, dividend, and corporate action facts
- governed instrument identity in `instrument_reference`
- persisted position, cash, and allocation snapshots
- a reconciliation harness that made the remaining `portfolio.` and `alocação` blockers explicit

The missing layer was temporal market data:

- market price as of a valuation date
- FX translation as of a valuation date
- provider provenance and retrievability independent from the position engine

Reverse-engineering evidence from the reference workbook and remote Apps Script payload already showed that the reference system separates:

- transaction facts
- instrument/reference facts
- market and FX inputs

## Decision

Add a new governed layer under `src/ov10/market/` with:

- canonical contracts for `MarketSnapshot` and `FxSnapshot`
- public-source adapters isolated from the engine
- persistence in SQLite through `market_snapshot` and `fx_snapshot`
- CLI refresh and report paths that inspect the persisted layer directly

### Provider boundary

The first governed providers are:

- `BrapiQuoteProvider` for Brazil-listed market quotes
- `BCBPTAXProvider` for official PTAX FX data

### Operational shape

Market/FX refresh is a separate workflow from workbook ingestion.

The position engine and batch persistence do not make live HTTP calls.

Instead:

1. workbook facts are persisted
2. market/FX snapshots are refreshed separately
3. reconciliation or valuation code can consume the persisted snapshot layer later

### First-pass support boundary

The first `brapi` pass only targets active canonical instruments that are:

- `stock_br`
- `fii`
- `bdr`
- `etf_br`

and already normalized to base currency `BRL`.

Unsupported categories stay explicit instead of being guessed:

- US stocks and ETFs
- crypto
- treasury
- `fund_br`

### FX rate choice

The governed PTAX snapshot stores:

- `bid`
- `ask`
- canonical `rate`

For the first pass, canonical `rate` is the midpoint of PTAX buy/sell for the selected bulletin.

Preference order:

- latest `Fechamento` bulletin for the latest available date in the requested lookback window
- otherwise latest bulletin timestamp in that window

### Authentication boundary

`brapi` authentication is supported by optional bearer token through:

- CLI `--brapi-token`
- environment variable `OV10_BRAPI_TOKEN`

This keeps the provider governed for bulk use while still allowing tokenless exploratory runs when the provider permits them.

## Consequences

Positive:

- the repo now has a persisted temporal market layer instead of placeholder gaps
- provider provenance is explicit and inspectable
- `portfolio.` and `alocação` can move from structural blockers to valuation-specific reconciliation work
- FX is now available for future `caixa` translation and international valuation logic

Tradeoffs:

- the first `brapi` pass does not cover every active instrument type in the fixture
- provider quotas/auth constraints can still limit bulk refreshes without a configured token
- this step does not yet project market value into `position_snapshot`, `book_position_snapshot`, or reconciliation outputs

## Follow-up

- consume persisted `market_snapshot` and `fx_snapshot` in valuation/reconciliation logic
- expand provider coverage and source-specific symbol mapping where needed
- add explicit market coverage diagnostics by instrument class and provider outcome

## Sources

- Brapi quote docs: https://brapi.dev/docs/acoes/list
- Banco Central PTAX dataset and API references:
  - https://dadosabertos.bcb.gov.br/en/dataset/dolar-americano-usd-todos-os-boletins-diarios
  - https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
