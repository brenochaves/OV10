# 2026-03-19 Instrument Reference Layer

## Objective

Close the identity side of `TASK-104` by turning observed source-code mappings into a governed canonical reference layer.

## What was added

- canonical table: `instrument_reference`
- normalized resolver from canonical facts
- CLI/report surface: `instrument-reference-report`

The layer sits above raw aliases:

- `instrument_mapping` remains the alias/provenance table
- `instrument_reference` becomes the canonical identity table

## Identity rules

The first pass uses only current OV10 canonical facts:

- transactions
- dividend receipts
- corporate actions

Normalization logic:

1. prefer typed observations over `unknown`
2. prefer known category values over `unknown`
3. prefer known currencies over fallback defaults
4. if multiple known values disagree, keep the most frequent value and mark the reference as conflicted
5. if an instrument only appears in corporate actions without typed facts, mark it as `observed_only`

## Real fixture result

Command flow used:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli persist-status-invest-xlsx data\OV10_base_2025.xlsx --database <temp-db>
.\.venv312\Scripts\python.exe -m ov10.cli instrument-reference-report --database <temp-db> --batch-id status_invest_xlsx:eb06d84422c5
```

Observed result for the checked-in fixture:

- `160` instrument references
- `160` active aliases
- identity statuses:
  - `observed_identity`: `160`

Type distribution:

- `stock_br`: `88`
- `fii`: `27`
- `stock_us`: `22`
- `etf_us`: `9`
- `crypto`: `4`
- `treasury_br`: `4`
- `bdr`: `3`
- `etf_br`: `2`
- `fund_br`: `1`

This means the current fixture did not produce unresolved or conflicting identities in the first pass.

## Example

For `ABEV3`, the reference layer now exposes:

- canonical code
- normalized type/category/currency
- alias list
- observation counts by fact family

That report path is sufficient for operators to inspect whether a code is supported structurally before the market-data layer exists.

## What this does not solve yet

This layer does not yet provide:

- market prices
- historical price series
- FX/PTAX series

So it helps close identity and mapping gaps, but not valuation gaps by itself.

## Next step

Build `market_snapshot` and `fx_snapshot` on top of this canonical reference surface.
