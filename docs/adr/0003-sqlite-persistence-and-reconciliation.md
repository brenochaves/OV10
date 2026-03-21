# ADR 0003: Persist Canonical Facts and Derived Snapshots in SQLite

Date: 2026-03-12

## Status

Accepted

## Context

Phase 1 created canonical contracts and an XLSX adapter, but the repo still had no durable storage, no idempotent import path, and no persisted reconciliation evidence.

The next step needs to support:

- repeatable imports of the same workbook without duplicating facts
- lineage from canonical facts back to source rows
- persisted position snapshots by engine version
- reconciliation evidence tied to a batch
- a local-first operational path that works immediately on this machine

## Decision

Use SQLite as the first governed persistence layer for the OV10 core.

Persist these artifacts:

- `import_batch`
- `source_record`
- `canonical_transaction`
- `canonical_dividend_receipt`
- `canonical_corporate_action`
- `position_snapshot`
- `batch_reconciliation`

Idempotency is enforced with deterministic identifiers and unique constraints. Derived artifacts such as snapshots and reconciliation reports are persisted by `batch_id + engine_version`, so the same source batch can be recomputed by future engine versions without re-importing raw facts.

## Consequences

- OV10 now has a durable and queryable audit trail
- the same workbook can be persisted repeatedly without duplicating canonical facts
- reconciliation output is no longer ephemeral CLI output only
- SQLite is acceptable for the current local-first phase, but PostgreSQL remains the likely long-term system-of-record target
