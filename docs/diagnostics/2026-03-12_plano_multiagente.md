# Multiagent Execution Plan - Phase 0 to Phase 2

Date: 2026-03-12

## Objective

Run OV10 as a governed multi-stream effort where each stream has explicit outputs, tests, and traceability.

## Agent Model

| Agent | Focus | Immediate Deliverable |
|---|---|---|
| A0 Orchestrator | scope, sequencing, architectural arbitration | approved roadmap and quality gates |
| A1 Spreadsheet RE | workbook mapping and portable rules | rule catalog and sheet inventory |
| A2 Apps Script RE | cloned script, workflow inventory, remote logic risks, online runtime bridge | script inventory, access report, and debug bridge |
| A3 Data Model | canonical schemas and invariants | entity contracts and enums |
| A4 Ingestion | source adapters and lineage | first Status Invest/XLSX adapter |
| A5 Ledger/Positions | transaction ledger, cash, positions | first reproducible position engine |
| A6 Dividends/CA | dividend events, receipts, hybrid event model | source model and reconciliation rules |
| A7 Fiscal | tax buckets and outputs | DARF/IR skeleton contracts |
| A8 QA/Reconciliation | scenario tests and consistency checks | synthetic and real-fixture test plan |
| A9 Research | external sources and DLombello benchmark | source benchmark and evidence log |
| A10 Documentation | technical docs and user operational docs | setup, runbook, usage docs, release notes |
| A11 Synthetic Data | fictitious workbooks, perturbation matrix, edge-case scenarios | synthetic fixture generator and scenario catalog |
| A12 Repository Steward | Git checkpoint cadence, sync audits, repo hygiene | checkpoint policy, sync audit tooling, loss-risk diagnostics |

## Governance Rules

- no engine rule is accepted without source lineage
- no adapter is accepted without schema validation
- no calculation module is accepted without business tests
- no external source is marked reliable without sample validation
- every structural decision should land with an ADR
- every user-facing operational flow should be documented in a runbook
- subagents must have disjoint ownership; duplicate exploration of the same artifact/question is not allowed
- prefer one explorer for runtime/reference evidence and one explorer for local codebase insertion points when parallelizing

## Phase Plan

### Phase 0-A - reverse engineering and evidence

Outputs:

- workbook reverse engineering
- Apps Script reverse engineering
- gap analysis
- source benchmark
- initial operational documentation

Exit criteria:

- evidence docs committed
- architecture direction approved

### Phase 1 - foundation

Outputs:

- package structure
- canonical schemas
- first adapter for current XLSX / Status Invest style import
- import batch model with lineage
- basic tests

Exit criteria:

- same input can be ingested idempotently
- schema validation is enforced

### Phase 2 - accounting core

Outputs:

- ledger
- cash movements
- position snapshots
- dividend receipts
- reconciliation reports

Exit criteria:

- position can be reproduced from ledger + events
- divergences are explicitly reported

## Required Artifacts Per Cycle

- diagnosis
- proposed change
- risks
- files changed
- tests added/executed
- unresolved gaps

## Definition of Done

A work item is only done when:

- code or docs are committed
- rationale is documented
- tests or validation evidence exist
- lineage/ownership is clear
