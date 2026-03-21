# 2026-03-19 Market Data Strategy

## Question

What does "live price" mean in the OV10 roadmap, and does the project really need realtime or non-public market data?

## Short answer

No tick-by-tick realtime feed is required for the current OV10 goals.

What the project needs is a governed way to answer:

- what is the best available market price for this instrument as of the valuation date?
- what was the daily price history for this instrument over a past interval?
- what FX rate should translate this instrument or cash balance into the base currency?

For the current parity path, delayed or end-of-day data is sufficient.

## What the reference runtime shows

Evidence from the captured remote payload:

- `obterAtivosCompletos()` materializes `ativosJSON` from the `ativos.` sheet.
- `executarCalcularTIRPortfolio()` calculates market value using:
  - `portfolioJSON[...].price`
  - overridden by `ativosJSON[ativo].price` when present
  - multiplied by `ativosJSON[ativo].fator_fx`
- the runtime still exposes integrations and utilities tied to market data, including:
  - `getStockinfoApi`
  - `atualizarIndicadores`
  - `FundamentusPonto`
  - `YahooClasses`
  - `obterCSVYahoo`
  - `exportarYahoo`

This confirms that the reference system already separates:

- transaction facts
- asset/reference facts
- market/FX inputs

## Why Google Finance is not enough

Google's own statement is explicit:

- historical `GOOGLEFINANCE` data cannot be accessed outside Sheets through Apps Script or API
- current data can still be accessed that way

This makes Google Sheets useful for the reference runtime, but not sufficient as the backend market source for OV10.

## Recommended source split

### 1. Instrument/reference layer

Source of truth:

- workbook/runtime evidence
- observed mappings already persisted by OV10

What belongs here:

- canonical instrument code
- aliases and source-specific symbols
- type/class/category
- currency
- market/country
- portfolio/book routing hints

### 2. Market data layer

Source of truth:

- public APIs with explicit provider provenance

Recommended provider order:

- `brapi.dev` for Brazil-listed assets, basic fundamentals, price history, and dividends
- Banco Central do Brasil PTAX for FX history
- Alpha Vantage as global fallback for adjusted history
- Yahoo only as non-governed fallback if we need exploratory coverage

## What this means for implementation

The next implementation step should not be "call an API from the valuation code."

It should be:

1. define market/reference contracts
2. persist normalized instrument identity
3. persist market and FX snapshots with source provenance
4. make reporting/reconciliation consume those persisted facts

## Relation to `caixa`

Synthetic data remains necessary for tests, but it does not replace the market layer.

For `caixa`, synthetic scenarios will be used to test:

- initial balances
- remittances and withdrawals
- manual credits and debits
- day trade buckets
- BRL/USD translation and PTAX timing

But the FX values themselves should come from a governed source, preferably BCB PTAX.

## Sources

- Google Workspace update on `GOOGLEFINANCE` historical access: https://workspaceupdates.googleblog.com/2016/09/historical-googlefinance-data-no-longer.html
- Brapi docs: https://brapi.dev/docs/acoes.mdx
- BCB PTAX docs: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
- Alpha Vantage docs: https://www.alphavantage.co/documentation/
