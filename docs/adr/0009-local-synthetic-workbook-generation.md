# ADR 0009: Prefer Local Synthetic Workbook Generation For Scenario Testing

Date: 2026-03-12

## Status

Accepted

## Context

OV10 needs controlled fictitious data to:

- test ingest, cash, reconciliation, and allocation behavior under varied conditions
- exercise edge cases such as corporate action cash attribution
- avoid depending on real user portfolio data for most automated tests

Synthetic data could be generated either through Google Sheets / Apps Script or directly in the local Python repository.

## Decision

Start with local synthetic workbook generation inside the Python repo.

Implementation rules:

- generate `.xlsx` workbooks that conform to the current OV10 ingestion contract
- keep scenarios versioned and deterministic
- expose generation through Python modules and CLI commands
- use the local path first because it is easier to validate in tests, CI, and offline operation

## Consequences

- OV10 now has a repo-governed way to generate fictitious input workbooks
- scenario testing can evolve without touching real data
- Apps Script or Google Sheets based generation remains possible later, but is not the first testing backbone
