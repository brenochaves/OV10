# ADR 0006: Use a Repo-Versioned Portfolio and Book Config File

Date: 2026-03-12

## Status

Accepted

## Context

The reference workbook has a rich `config.carteiras` and `config.books` layer, but the current XLSX input adapter does not carry that configuration. OV10 still needed a governed way to define:

- portfolios
- books
- account-to-portfolio assignment rules
- book routing rules by instrument type

Delaying this until a full spreadsheet-config adapter exists would leave the new account-aware ledger without a controlled allocation model.

## Decision

Introduce a repo-versioned TOML file at `config/ov10_portfolio.toml` as the current source of truth for portfolio/book configuration.

Current behavior:

- portfolios and books are loaded from the TOML file
- account assignment uses explicit pattern rules, with a default portfolio fallback
- book routing uses configured instrument-type rules
- persisted account position snapshots are projected into `book_position_snapshot`

## Consequences

- OV10 now has versioned, reviewable configuration under source control
- portfolio/book logic is no longer implicit or spreadsheet-only
- the default config is intentionally conservative and should be treated as a governed baseline, not as a final user-specific allocation policy
- a future adapter from `config.carteiras` / `config.books` can target the same contracts instead of replacing them
