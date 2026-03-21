# ADR 0005: Derive Broker Account and Cash Ledger from Canonical Facts

Date: 2026-03-12

## Status

Accepted

## Context

The reference workbook has an explicit `caixa` layer and a strong portfolio/accounting decomposition. OV10 still lacked any governed cash model, even after canonical facts and position snapshots were in place.

The current XLSX adapter already exposes enough information to derive a first useful cash ledger:

- trade cash effects
- net dividend receipts
- cash components from corporate actions
- broker names for most cash-producing records

## Decision

Introduce a derived cash layer composed of:

- `account_registry`
- `cash_movement`
- `cash_balance_snapshot`

Current account derivation rules:

- broker names observed in transactions and dividend receipts create broker accounts
- corporate action cash without broker attribution lands in a system account
- cash balances are derived by summing persisted cash movements per account and currency

## Consequences

- OV10 now has a first-class cash ledger tied to the same import batch
- broker-level cash balances can be inspected from the persisted batch report
- unresolved broker attribution for some corporate action cash remains visible as a reconciliation warning instead of being silently dropped
- portfolio/book allocation still requires a dedicated configuration adapter and is not considered solved by this step
