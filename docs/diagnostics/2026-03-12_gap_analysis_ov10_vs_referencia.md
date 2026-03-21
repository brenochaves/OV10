# Gap Analysis - OV10 Current Repo vs Reference System

Date: 2026-03-12

## Current OV10 State

Current repo contents:

- 5 Python files at repo root
- 1 local input workbook
- no package structure
- no project metadata
- no lockfile
- no tests
- no migrations
- no canonical schemas
- no persistence layer
- no ADRs
- no CI

## Evaluation of Current Python Files

| File | Current Role | Keep? | Decision |
|---|---|---|---|
| `leitor_planilha.py` | reads current XLSX and normalizes a few columns | partial | reuse as seed for first adapter only |
| `consolidar_posicao.py` | simplistic aggregation by asset | no | discard as portfolio engine |
| `exportador.py` | writes output XLSX | low | replace later with reporting/export layer |
| `main.py` | script entrypoint | no | replace with package CLI/jobs |
| `utils.py` | placeholder | no value yet | ignore |

## Why `consolidar_posicao.py` Is Not a Valid Engine

Observed limitations:

- no chronological ledger reconstruction
- no idempotent ingestion
- no portfolio/book/account dimension
- no tax lots
- no cash model
- no proper corporate action treatment
- no reconciliation against source positions
- no explicit schema contracts

The generated output showed materially distorted average cost and PnL values for multiple assets. This confirms the script is exploratory only.

## Reference vs Current OV10

| Domain | Reference System | Current OV10 | Gap | Required Action |
|---|---|---|---|---|
| input schemas | broad and explicit | ad hoc | very high | define canonical schemas |
| portfolios/books | explicit config model | absent | very high | create investor/portfolio/book/account model |
| cash | explicit sheet and formulas | absent | high | add cash movement model |
| processed asset facts | `portfolio.` / `ativos.` style layers | absent | very high | create ledger + positions + reference data |
| dividends | explicit input/output panels | partial raw load only | high | create dividend events + receipts |
| tax | DARF and DIRPF outputs | absent | very high | design tax engine contracts |
| governance | versioning and operational flows exist | absent | very high | add docs, ADRs, tests, audit trail |
| external adapters | multiple source assumptions | absent | high | build anti-corruption adapters |

## Reuse Strategy

Recommended stance:

- do not start from zero in knowledge
- do start from zero in domain core implementation

What to reuse:

- reference workbook decomposition
- current XLSX input headers and examples
- conversion mapping concept
- feature naming from Apps Script menus

What to rebuild:

- canonical data model
- ingestion architecture
- position engine
- dividend engine
- cash engine
- reconciliation layer
- tax layer
- API/reporting layers

## Immediate Architecture Direction

Phase 1 foundation:

- `src/ov10/`
- canonical schemas
- adapters for current XLSX / Status Invest style inputs
- domain entities for investor/portfolio/book/account/instrument
- immutable import batches with source metadata
- ledger + cash + corporate action placeholders
- tests for real scenarios

Phase 2 core:

- position snapshots
- dividend receipts
- reconciliation rules
- allocation/report outputs

Phase 3 fiscal:

- monthly BR tax buckets
- DARF support
- annual IR support

## Decision

The current repo should be treated as exploratory code plus fixture data.

Recommended professional path:

- preserve the current scripts as historical reference
- create a new structured OV10 core beside them
- port only validated rules and contracts into the new codebase
