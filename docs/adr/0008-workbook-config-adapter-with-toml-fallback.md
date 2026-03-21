# ADR 0008: Support Workbook Configuration Import With TOML Fallback

Date: 2026-03-12

## Status

Accepted

## Context

OV10 already had a governed TOML configuration for portfolios and books, but the reference workbook contains a richer `config.books` and `config.carteiras` layer that should influence the long-term allocation model.

The checked-in reference workbook is also a template-like artifact:

- `config.books` contains portable book definitions
- `config.carteiras` exposes portfolio slots, but in the current artifact they remain mostly generic template entries such as `Carteira #1`
- account-to-portfolio assignment rules are not directly portable from the current workbook artifact

The current OV10 allocation engine still routes by `InstrumentType`, not by the full spreadsheet metadata matrix.

## Decision

Extend `load_portfolio_book_config()` so it accepts:

- repo-versioned `.toml` files
- workbook-based `.xlsx` / `.xlsm` configuration sources

Normalization rules for workbook config:

- import `config.books` rows into current `BookDefinition` contracts
- use supported instrument-type mappings where the current OV10 engine can route safely
- keep unsupported workbook books imported but inactive
- append an active `Sem Book` fallback to absorb unknown or unsupported routing cases
- when `config.carteiras` looks like an unconfigured template, reuse portfolio and account-assignment data from the governed TOML fallback

## Consequences

- OV10 can now use the reference workbook as a configuration source without dropping the governed TOML baseline
- the current reference workbook maps to `11` persisted books when used as config
- some workbook concepts still do not project fully because the current engine does not yet route by richer asset metadata
- the TOML file remains a valid and supported fallback path, not dead configuration
