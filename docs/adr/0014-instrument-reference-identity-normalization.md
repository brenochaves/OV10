# ADR 0014: Instrument Reference Identity Normalization

Date: 2026-03-19

## Status

Accepted

## Context

By 2026-03-19, OV10 already persisted observed source-code mappings in `instrument_mapping`, but it still lacked a governed canonical layer that answered:

- what is the durable canonical instrument identity for a code observed in canonical facts?
- how should conflicts between observed types/categories be recorded?
- how can operators inspect the normalized state without reading raw canonical tables?

This was the main acceptance gap left in `TASK-104`.

## Decision

Keep `instrument_mapping` as the alias/observed-code layer and add a new canonical layer `instrument_reference`.

### Layers

`instrument_mapping`

- one row per observed `source_system + source_code`
- keeps alias-style provenance and batch lineage

`instrument_reference`

- one row per canonical instrument code
- stores normalized identity fields:
  - `canonical_code`
  - `instrument_type`
  - `asset_category`
  - `currency`
  - `reference_origin`
  - `identity_status`
  - `first_batch_id`
  - `last_batch_id`
  - `notes`

### Normalization rules

The first reference pass is built only from canonical OV10 facts:

- `canonical_transaction`
- `canonical_dividend_receipt`
- `canonical_corporate_action`

Resolution rules:

1. prefer known instrument types over `unknown`
2. prefer known asset categories over `unknown`
3. prefer known currency over the default fallback
4. if multiple known values disagree, choose the most frequent value and mark the record as conflicted
5. if only corporate-action references exist and no typed facts exist, mark the record as `observed_only`

### Identity statuses

- `observed_identity`
- `observed_with_conflict`
- `observed_only`

### Reporting

Expose the normalized state through a governed CLI/report path:

- `ov10.cli instrument-reference-report`

## Consequences

Positive:

- `TASK-104` now has a durable reference layer, not only observed aliases.
- Operators can inspect normalized identity and alias lineage without querying raw tables directly.
- The next market-data step can build on stable canonical instruments instead of raw source codes.

Tradeoffs:

- This first pass does not yet fetch market prices or FX rates.
- Cross-batch normalization remains conservative and alias-driven.
- A later market/provider task is still required for valuation parity in `portfolio.` and `alocação`.

## Follow-up

- Add market and FX snapshot contracts on top of `instrument_reference`.
- Introduce provider adapters for public market and FX sources.
- Use the normalized reference layer as the join surface for valuation and reporting.
