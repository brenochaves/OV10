# Reverse Engineering - Reference Workbook

Date: 2026-03-12

## Scope

Artifact analyzed:

- local workbook export in `ov10_codex_handoff`

Method:

- workbook inventory
- sheet dimensions
- formula density
- sampling of headers and representative formulas
- portability classification for OV10

## Executive Summary

The workbook is not a simple reporting spreadsheet. It already encodes a layered system:

- input/staging
- configuration
- processed portfolio state
- reporting and dashboards
- tax outputs

The strongest reusable value is not the spreadsheet implementation itself. The reusable value is:

- domain decomposition
- config model for portfolios/books
- input taxonomy
- processed views to be replicated in Python
- fiscal output expectations

Important correction after deeper compatibility review:

- the offline `.xlsx` export must not be treated as functionally equivalent to the online Google Sheets version
- it is a strong structural and formula-reference artifact, but not an authoritative executable replica

Evidence found in the checked-in offline workbook:

- `18184` formulas were exported as `__xludf.DUMMYFUNCTION(...)`
- `14899` formulas still reference `QUERY(...)`
- `4544` formulas still reference `GOOGLEFINANCE(...)`
- dynamic-array style `FILTER(...)`, `SORT(...)`, and `COUNTUNIQUE(...)` patterns also appear heavily

This means the export preserved a large amount of business structure, but it also preserved many Google Sheets-specific expressions in a degraded compatibility state.

## Sheet Inventory

| Sheet | Category | Role | Rows x Cols | Formulas | Port to OV10? | Notes |
|---|---|---:|---:|---:|---|---|
| `leiame` | meta | product/version info | 44 x 2 | 3 | partial | useful only for version/context |
| `portfolio` | output | main portfolio dashboard | 343 x 121 | 4140 | logic only | high-value output design, not implementation |
| `summary` | output | executive summary panel | 555 x 25 | 34 | logic only | output KPI expectations |
| `rendimentos` | output | dividends/income panel | 310 x 31 | 5448 | yes | useful for dividend/reporting specs |
| `op.normal` | input | normal trade ledger | 2064 x 45 | 1 | yes | core input schema inspiration |
| `op.daytrade` | input | day trade ledger | 2035 x 46 | 2 | yes | fiscal split is explicit |
| `proventos` | input | received dividends/income | 2036 x 34 | 1 | yes | canonical dividend receipt seed |
| `caixa` | processing | cash movement register and derived cash flow | 304 x 37 | 210 | yes | strong candidate for OV10 cash engine |
| `radar` | output | monitoring and watchlist | 308 x 103 | 10274 | partial | analytics layer, later phase |
| `alocacao` | output | allocation/rebalance view | 623 x 75 | 4357 | yes | strong business requirement |
| `extratos` | input | extract/combined raw views | 500 x 25 | 0 | partial | likely staging/export helper |
| `darf` | output/fiscal | monthly tax view | 64 x 64 | 6 | yes | target output for BR tax engine |
| `dirpf` | output/fiscal | annual tax/IR support | 1000 x 37 | 1 | yes | target annual output |
| `config.parametros` | config | calculation toggles and global params | 79 x 16 | 0 | yes | maps well to OV10 settings tables |
| `config.outros` | config | non-standard asset registry | 51 x 6 | 0 | yes | useful as manual instrument registry |
| `config.carteiras` | config | portfolio configuration | 106 x 231 | 1648 | yes | very high-value reference |
| `config.books` | config | book matrix/allocation model | 574 x 111 | 3517 | yes | very high-value reference |
| `scripts` | utility | script/button mapping | 20 x 3 | 0 | no | Apps Script/UI operational detail |
| `portfolio.` | processing | processed backend-like table | 303 x 68 | 1421 | yes | likely closest spreadsheet equivalent to canonical position view |
| `ativos.` | processing/reference | price/fx/reference asset layer | 1000 x 25 | 302 | yes | price/reference service boundary |
| `carteiras.` | processing | portfolio asset matrix | 754 x 37 | 12 | yes | links assets to portfolios |
| `carteiras..` | output | portfolio summary by enabled portfolio | 16 x 9 | 90 | yes | aggregation target |
| `fundamentus.` | external ref | imported fundamentals data | 137 x 21 | 0 | optional | source-specific adapter only |
| `fundsexplorer.` | external ref | imported FII data | 33 x 26 | 0 | optional | source-specific adapter only |

## Important Formula Patterns

Observed patterns with strong portability value:

- `caixa` computes derived cash flow by reconciling cash rows with `op.normal`, `op.daytrade`, and `proventos`.
- `config.books` contains a real allocation matrix and book metadata, not just labels.
- `portfolio.` behaves like a processed fact table with quantity, market value, open PnL, FX, and asset metadata.
- `ativos.` separates market/reference data from transaction logic and uses pricing/fx fallbacks.
- `darf` and `dirpf` show clear fiscal output targets that OV10 should eventually reproduce.

## Compatibility Boundary: Offline Export Vs Online Sheet

The offline workbook is useful, but it is not a faithful runtime substitute for the Google Sheets original.

Concrete evidence from the exported artifact:

- `rendimentos`: `5448` formulas, `5103` exported as `__xludf.DUMMYFUNCTION`
- `config.books`: `3517` formulas, `2872` exported as `__xludf.DUMMYFUNCTION`
- `ativos.`: `302` formulas, `259` exported as `__xludf.DUMMYFUNCTION`
- `caixa`: `210` formulas, `118` exported as `__xludf.DUMMYFUNCTION`

Interpretation:

- many online formulas survived only as placeholders or partially degraded expressions in Excel
- Google Sheets-specific services such as `GOOGLEFINANCE` are not a reliable offline execution path
- dynamic arrays and query-style calculations are not safe to treat as executable truth in the `.xlsx` export

Working rule for OV10:

- treat the offline workbook as a high-value reverse-engineering source for structure, semantics, contracts, and output expectations
- do not assume it reproduces the same live behavior as the online sheet

## Portable Business Concepts

High-value concepts to port:

- explicit separation of `op.normal` vs `op.daytrade`
- explicit `caixa` domain
- `portfolio -> books -> assets` configuration model
- processed asset table separated from raw operations
- dedicated fiscal outputs
- dashboard-level allocation and dividend reporting

## What Should Not Be Ported As-Is

- spreadsheet formulas themselves
- direct dependence on `GOOGLEFINANCE`
- UI-specific tab/button behavior
- any hidden spreadsheet-only operational coupling

## Risks and Limitations

- formula-heavy sheets encode logic implicitly; direct port without naming the rules would create reimplementation risk
- some logic may live outside the workbook, in Apps Script or remote-loaded script code
- public materials from DLombello can inform scope, but are not authoritative for the exact user artifact

## Recommended Extraction Order

1. input schemas from `op.normal`, `op.daytrade`, `proventos`, `caixa`
2. config schemas from `config.parametros`, `config.carteiras`, `config.books`
3. processed facts from `portfolio.` and `ativos.`
4. output contracts from `alocacao`, `rendimentos`, `darf`, `dirpf`
5. later analytics from `radar` and `summary`
