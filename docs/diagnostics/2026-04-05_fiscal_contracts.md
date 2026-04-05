# Fiscal Contracts

Date: 2026-04-05

## Goal

Close `TASK-105` with a first governed fiscal contract layer aligned to the
reference workbook targets `darf` and `dirpf`.

## Evidence Used

Workbook structure:

- `darf` row `5`
- `dirpf` row `4`

Captured runtime descriptors from `v61_controle_64.js`:

- `DARF().rangeInvestidores = A9:A15`
- `DARF().rangeCabecalho = C5:BL5`
- `DARF().rangeDados = C7:BL`
- `DIRPF().rangeInvestidores = A7:A13`
- `DIRPF().rangeCabecalhoBensDireitos = D4:I4`
- `DIRPF().rangeCabecalhoDividaOnus = L4:Q4`
- `DIRPF().rangeCabecalhoRendimentosIsentos = T4:X4`
- `DIRPF().rangeCabecalhoTributacaoExclusiva = AA4:AE4`
- `DIRPF().rangeCabecalhoCarneLeao = AH4:AK4`

Runtime evidence also confirms explicit fiscal modules and entrypoints:

- `calcularDARF`
- `calcularDIRPF`
- `definirPadraoDARFDIRPF`

## Delivered Layer

Code paths:

- `src/ov10/fiscal/models.py`
- `src/ov10/fiscal/contracts.py`
- `src/ov10/fiscal/__init__.py`
- `src/ov10/cli.py`
- `tests/test_fiscal_contract_report.py`

Operator command:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli fiscal-contract-report
```

## Current Safe Coverage

### DARF

What the first contract layer already exposes safely:

- workbook-aligned field order
- monthly sale volume by month
- sale-volume split for:
  - `acao_vol_alienacao`
  - `etf_vol_alienacao`
  - `vol_alienacao`

What remains intentionally unsupported:

- realized gains
- exempt thresholds and exempt gains
- day-trade taxable basis
- IRRF and carryforward saldo
- futures, options, gold, and termo buckets

Observed on the checked-in fixture:

- `253` sell transactions
- DARF basis rows spanning from `2019-08-31` to `2025-05-31`

### DIRPF

What the first contract layer already exposes safely:

- `21` `bens_direitos` candidate entries from open positions
- `1` `tributacao_exclusiva` candidate entry from JCP in the 2025 base year

Section status on the fixture:

- `bens_direitos` -> `partial`
- `divida_onus` -> `missing`
- `rendimentos_isentos` -> `partial`
- `tributacao_exclusiva` -> `partial`
- `carne_leao` -> `missing`

## Declared Gaps

The contract report now makes these dependencies explicit:

- `missing_tax_lot_engine`
- `unsupported_tax_asset_classes`
- `missing_dirpf_tax_code_mapping`
- `missing_prior_year_fiscal_snapshot`
- `missing_manual_fiscal_inputs`

## Validation

- `python -m pytest -q tests/test_fiscal_contract_report.py`
- `python -m pytest -q` -> `41 passed`
- `python -m ruff check .` -> green
- `npm run typecheck:python` -> `0 errors`

## Conclusion

`TASK-105` is satisfied in the intended first-pass shape.

OV10 now has:

- concrete fiscal output contracts
- a reproducible fiscal report path
- explicit boundaries between current accounting evidence and missing fiscal
  rule dependencies

What it still does not have is a full tax engine, and this diagnostic keeps
that boundary explicit.
