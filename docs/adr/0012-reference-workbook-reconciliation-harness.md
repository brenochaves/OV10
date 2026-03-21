# ADR 0012: Reference Workbook Reconciliation Harness

Date: 2026-03-19

## Status

Accepted

## Context

The OV10 core needed a reproducible way to compare its current outputs against the checked-in reference workbook without pretending that the offline `.xlsx` export is a faithful runtime twin of the Google Sheets + Apps Script system.

By 2026-03-19, the repo already had:

- the canonical ingestion path for `data/OV10_base_2025.xlsx`
- governed persistence and reporting
- reverse-engineering evidence for the reference workbook structure
- an explicit compatibility warning that the offline export is degraded in several areas

What was still missing was a disciplined answer to: "how far is OV10 from the reference workbook outputs right now?"

## Decision

Adopt a selective reconciliation harness instead of claiming full workbook parity.

The harness will:

- be versioned in code and exposed through the CLI
- use the checked-in fixture and reference workbook as reproducible inputs
- compare current OV10 coverage against selected reference workbook areas:
  - `portfolio.`
  - `caixa`
  - `alocação`
  - `rendimentos`
- classify each reference field or metric as:
  - `expected`
  - `explained`
  - `blocking`
- use workbook formulas and structural evidence when cached offline values are not reliable enough

For `rendimentos`, the harness is allowed to reproduce the workbook's month-window logic directly from canonical dividend receipts, because the relevant formula intent is explicit in the exported workbook.

## Consequences

Positive:

- `TASK-103` can be closed with a real, reproducible artifact instead of a vague narrative.
- The repo now has an explicit parity baseline for future work.
- Gaps for market data, allocation/rebalance logic, and manual cash inputs are visible and traceable.

Tradeoffs:

- This is not full runtime parity with the live Google Sheets deployment.
- Some workbook areas are assessed by contract and formula intent, not by cached exported values alone.

Follow-up:

- Use this harness before claiming parity improvements in positions, cash, allocation, or income reporting.
- Treat `TASK-104` as the next priority because market/instrument reference gaps dominate the remaining blockers in `portfolio.` and `alocação`.
