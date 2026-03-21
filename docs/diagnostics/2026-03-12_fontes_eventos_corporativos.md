# Benchmark Inicial - Fontes de Eventos Corporativos

Date: 2026-03-12

## Goal

Identify candidate public/free sources for dividends and corporate actions to support OV10 in hybrid mode.

Important rule:

- no source below is treated as proven coverage for all cases
- this document is an initial benchmark only
- live validation with sample tickers/events is still required

## Sources Reviewed

| Source | Official Link | Likely Coverage | BR Focus | Cost/Auth | Current Assessment |
|---|---|---|---|---|---|
| Status Invest exports | user workflow, no public API assumed | user-level consolidated data, dividends, applied events | high for user workflow | manual/semi-manual | best practical source for this user in short term |
| Brapi | `https://brapi.dev/` | B3 market data and some dividend endpoints | high | public API tiers | promising for BR dividends/prices, corporate action coverage still unverified |
| B3 Developers | `https://developers.b3.com.br/apis` | official B3 APIs/portals, custody/investor related products | high | auth/product dependent | relevant official ecosystem, but not yet validated as simple free corporate action feed |
| Alpha Vantage | `https://www.alphavantage.co/documentation/` | global historical data with split/dividend adjusted datasets | medium | free tier + key | useful as auxiliary source, BR edge cases still uncertain |
| Polygon | `https://polygon.io/docs/` | corporate actions and reference data for supported markets | low/medium for BR | key/paid tiers | useful benchmark source, probably not primary BR source |
| Finnhub | `https://finnhub.io/docs/api` | dividends/splits/reference endpoints | low/medium for BR | free + paid tiers | useful benchmark source, not yet validated for BR coverage |
| Fundamentus | `https://www.fundamentus.com.br/` | BR fundamentals website | high | website, not API-first | useful fallback/reference, not ideal canonical source |
| Funds Explorer | `https://www.fundsexplorer.com.br/` | FII-focused website | high for FII context | website, not API-first | useful fallback/reference, not ideal canonical source |

## Working Conclusions

1. There is no validated single public/free source here that should be trusted as sole truth for BR corporate actions.
2. For this user, the best short-term strategy is still hybrid:
   - consume user-level consolidated data when available
   - enrich with public/free sources
   - support governed manual overrides
3. Dividends are easier to source than full corporate action chains.
4. The hardest events remain:
   - bonus issues
   - subscriptions
   - spin-offs
   - ticker changes
   - amortizations
   - merger/incorporation edge cases

## Recommended OV10 Strategy

Short term:

- trust Status Invest exports as a practical user-centric input when available
- ingest them with full lineage
- allow manual correction tables

Medium term:

- add source confidence per event
- reconcile public data vs user-level source
- maintain canonical `corporate_action` and `dividend_event` tables

Long term:

- build event coverage tests by event type and market
- score each source by completeness, latency, and maintenance cost

## Validation Backlog Still Needed

- pick real BR examples for split, reverse split, bonus, subscription, spin-off, ticker change, amortization
- test source latency and historical coverage
- test whether event dates and ratios match user holdings history
- define fallback hierarchy and conflict resolution rules
