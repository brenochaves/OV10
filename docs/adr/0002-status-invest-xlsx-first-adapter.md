# ADR 0002: Use the Current XLSX Workbook as the First Supported Adapter

Date: 2026-03-12

## Status

Accepted

## Context

The user already has a functioning real-world workflow based on exported or curated workbook data. The shortest path to a governed OV10 core is to ingest that real input first instead of waiting for broader broker/API automation.

## Decision

Implement the first formal adapter around `data/OV10_base_2025.xlsx` semantics:

- `Operações`
- `Proventos`
- `Conversoes_Mapeadas`

This adapter emits canonical transactions, dividend receipts, and corporate actions with source lineage.

## Consequences

- OV10 starts from real user data rather than hypothetical sources
- tests can run against a stable fixture immediately
- later adapters for Status Invest exports, broker notes, or APIs can target the same canonical contracts
