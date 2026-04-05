# ADR 0021: First DARF/DIRPF Contracts

Date: 2026-04-05

## Status

Accepted

## Context

The reference workbook and captured runtime clearly expose fiscal targets:

- `darf` as the monthly tax view
- `dirpf` as the annual personal-income-tax support view

By this point, OV10 already had:

- governed ingestion of trades and dividend receipts
- position snapshots
- market and FX snapshot layers
- reconciliation evidence strong enough to keep accounting and fiscal scopes
  separate

What was still missing was a contract-first fiscal layer that could:

- name the target outputs explicitly
- state what the current core can already seed safely
- state what still depends on missing tax rules, mappings, or manual inputs

## Decision

Add a first fiscal contract layer under `src/ov10/fiscal/`.

The first slice is intentionally contract-first, not a full tax engine.

It includes:

1. explicit DARF contract models
   - monthly sale-volume basis by month
   - workbook-aligned DARF field order
   - supported vs unsupported field lists

2. explicit DIRPF contract models
   - `bens_direitos` candidate entries from open positions
   - `tributacao_exclusiva` candidate entries from JCP receipts
   - section-level support reporting for:
     - `bens_direitos`
     - `divida_onus`
     - `rendimentos_isentos`
     - `tributacao_exclusiva`
     - `carne_leao`

3. an operator-visible CLI
   - `ov10.cli fiscal-contract-report`

4. explicit dependency gaps
   - missing tax-lot engine
   - unsupported DARF asset classes
   - missing DIRPF tax-code and payer mapping
   - missing prior-year fiscal snapshots
   - missing manual fiscal inputs

## Consequences

Positive:

- OV10 now has canonical fiscal output contracts without pretending to calculate
  DARF or DIRPF completely.
- Scope boundaries between accounting and fiscal layers are now explicit in
  code, tests, and docs.
- Follow-up work can target named missing dependencies instead of vague “tax
  support later”.

Trade-offs:

- the first contract layer is intentionally partial
- gains, loss carryforward, IRRF, and actual tax due are not calculated yet
- several DIRPF codes and payer fields remain unmapped

## Validation

- `tests/test_fiscal_contract_report.py`
- `python -m pytest -q` -> `41 passed`
- `python -m ruff check .` -> green
- `npm run typecheck:python` -> `0 errors`
