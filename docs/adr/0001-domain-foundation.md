# ADR 0001: Create a Structured OV10 Domain Foundation

Date: 2026-03-12

## Status

Accepted

## Context

The repository contained exploratory Python scripts and fixture spreadsheets, but no package structure, no canonical schemas, no tests, and no governed path to evolve into a portfolio accounting engine.

## Decision

Create a new implementation foundation under `src/ov10/` with:

- canonical domain enums and models
- source adapters isolated under `ingestion/`
- position engine isolated under `positions/`
- project metadata in `pyproject.toml`
- tests under `tests/`

The existing root-level scripts remain as legacy exploratory artifacts and are not treated as the future domain core.

## Consequences

- future work can evolve with contracts, tests, and versioned modules
- legacy scripts remain available for reference and fixture derivation
- the codebase gets a clean migration path without destructive rewrite of user artifacts
