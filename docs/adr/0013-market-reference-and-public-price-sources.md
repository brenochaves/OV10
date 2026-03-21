# ADR 0013: Market Reference Layer and Public Price Source Strategy

Date: 2026-03-19

## Status

Accepted

## Context

The current OV10 reconciliation baseline shows that `portfolio.` and `alocação` remain blocked mainly because the repo still lacks a governed market/reference layer.

Reverse-engineering evidence already shows that the reference system separates transaction logic from market/reference logic:

- the workbook uses `ativos.` as a distinct processing/reference area for prices, FX, and asset metadata
- the captured remote runtime exposes `obterAtivosCompletos()`
- portfolio calculations use `portfolioJSON.price` and override it with `ativosJSON.price` when available
- the runtime also uses `fator_fx` to translate market values

At the same time, "market data" and "instrument identity" are not the same problem:

- instrument identity is mostly structural and can be reverse-engineered from workbook/runtime evidence
- prices and FX are temporal data and must come from an external market data source

## Decision

Adopt a two-layer design:

1. `instrument_reference`
2. `market_snapshot` plus `price_history` and `fx_history`

The first implementation will not require tick-by-tick realtime data.

The initial target is:

- delayed or end-of-day market price for current valuation
- daily historical series for backfills and reconciliation
- official FX/PTAX history for cash translation

### Source strategy

Use public or low-friction sources with explicit provider boundaries.

Primary source choices:

- Brazil-listed instruments: `brapi.dev`
- FX/PTAX: Banco Central do Brasil PTAX OData
- global fallback history: Alpha Vantage

Non-primary sources:

- Google Finance inside Google Sheets may remain useful as runtime evidence, but not as the OV10 backend market source
- Yahoo Finance may be used as an exploratory or compatibility fallback, but not as a governed source of truth

### Why

`GOOGLEFINANCE` is not enough for the backend path:

- Google states that historical `GOOGLEFINANCE` data cannot be accessed outside Sheets via Apps Script or API
- only current data remains accessible that way

That means the reference workbook can still rely on `GOOGLEFINANCE` interactively, but OV10 cannot build a professional backend on top of it for reproducible historical valuation.

### Minimum contracts

The first governed market layer must support at least:

- instrument code and aliases
- normalized instrument class/type
- market/country/currency
- source-specific symbol mapping
- last price as of a timestamp
- daily price history
- split/dividend-adjusted history when available
- FX rate as of a timestamp
- source, retrieval timestamp, and confidence/provenance

## Consequences

Positive:

- `TASK-104` gets a clear boundary between static reference data and temporal market data.
- `portfolio.` and `alocação` can be improved without mixing external HTTP calls into the position engine.
- `caixa` follow-up work can reuse the same FX layer for BRL/USD translation and PTAX-based reporting.

Tradeoffs:

- One provider will not cover every market, every asset class, and every corporate action nuance.
- Provider abstraction adds up-front structure before immediate parity gains.
- Free/public sources can have quota, delay, or symbol-coverage limitations.

## Follow-up

- Build domain contracts for `instrument_reference`, `market_snapshot`, and `fx_snapshot`.
- Add provider adapters behind a governed interface, starting with `brapi.dev` and BCB PTAX.
- Use captured workbook/runtime evidence to define fields and mapping semantics before claiming parity in `portfolio.` and `alocação`.

## Sources

- Google Workspace update on `GOOGLEFINANCE` historical access: https://workspaceupdates.googleblog.com/2016/09/historical-googlefinance-data-no-longer.html
- Brapi docs: https://brapi.dev/docs/acoes.mdx
- BCB PTAX docs: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
- Alpha Vantage docs: https://www.alphavantage.co/documentation/
