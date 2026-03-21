# ADR 0004: Seed Instrument Mapping from Observed Source Codes

Date: 2026-03-12

## Status

Accepted

## Context

The reference system has a strong mapping/configuration layer. OV10 did not yet have a governed place to record source ticker aliases, canonical codes, or future overrides.

Waiting for a complete mapping subsystem would slow down persistence and reconciliation unnecessarily.

## Decision

Introduce an `instrument_mapping` table and seed it automatically from observed source codes during import.

Initial behavior:

- source code maps to itself as canonical code
- mapping origin is recorded as `observed_identity`
- unknown instrument types can later be upgraded when a stronger observation arrives
- future manual overrides can land in the same table instead of creating a parallel mapping mechanism

## Consequences

- OV10 gains a first-class mapping surface immediately
- later adapters can reuse the same table for aliasing and normalization
- the current mapping layer is intentionally conservative and does not yet solve all cross-source symbol normalization cases
