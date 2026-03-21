# Reference Workbook Reconciliation

Date: 2026-03-19

## Scope

This diagnostic records the first governed reconciliation pass between:

- source fixture: `data/OV10_base_2025.xlsx`
- reference workbook: `ov10_codex_handoff/Cópia de v6.4_Controle de Investimentos (Alpha).xlsx`
- config baseline: `config/ov10_portfolio.toml`

Command:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli reference-workbook-reconciliation data\OV10_base_2025.xlsx --reference-workbook "ov10_codex_handoff\Cópia de v6.4_Controle de Investimentos (Alpha).xlsx" --config config\ov10_portfolio.toml
```

## Result

Current summary:

- `1` area classified as `expected`
- `0` areas classified as `explained`
- `3` areas classified as `blocking`

Runtime counts used in this pass:

- `1025` transactions
- `1486` dividend receipts
- `5` corporate actions
- `21` aggregate position snapshots
- `21` account position snapshots
- `21` book position snapshots
- `2493` cash movements

## Findings

### `rendimentos`

Classification: `expected`

What is already strong:

- OV10 already holds the row facts needed by the workbook panel:
  - asset
  - payment date
  - event type
  - net amount
- OV10 can already reproduce the workbook's "Últimos 12 meses" monthly windows from canonical dividend receipts.

Current computed net series for the fixture:

- `2025-06-30`: `6.28`
- `2025-05-31`: `8.94`
- `2025-04-30`: `13.84`
- `2025-03-31`: `7.24`
- later months in the workbook window are `0` for this fixture

### `portfolio.`

Classification: `blocking`

What already exists:

- `ativo`
- `corretora`
- `qtd_atual`
- `pm_atual`
- `vlr_investido`

Main blockers:

- no governed market reference yet for `market_cod`, `nome_pregao`, `price`, `change`, `changepct`
- no sector/subsector metadata
- no exported matrix equivalent for the workbook's multi-carteira columns
- no investor dimension separated from account/carteira

Coverage snapshot:

- `5` matched fields
- `5` explained partial fields
- `15` blocking fields

### `caixa`

Classification: `blocking`

What already exists:

- `corretora`
- `moeda`
- `proventos`
- `saldo`

Main blockers:

- no `saldo_inicial`
- no manual `rem/saq`
- no manual `cre/deb`
- no day-trade bucket equivalent
- no FX cash layer
- no separate investor dimension

Coverage snapshot:

- `4` matched fields
- `1` explained partial field
- `6` blocking fields

### `alocação`

Classification: `blocking`

What already exists:

- books as governed entities
- invested value by book from cost basis

Main blockers:

- no market value layer
- no adjustment/recommendation engine
- no FX cash integration in the book dashboard
- no total profit by book

Coverage snapshot:

- `2` matched fields
- `2` explained partial fields
- `5` blocking fields

## Interpretation

This pass was enough to close the first reconciliation task professionally.

It proves that:

- the repo now has a reproducible parity baseline
- `rendimentos` is already on strong conceptual footing
- the next dominant blockers are exactly where expected:
  - market and instrument reference
  - manual cash input classes
  - rebalance/allocation dashboard outputs

## Next Step

Recommended next focus: `TASK-104`

Reason:

- the market/instrument reference layer unlocks the largest number of remaining blockers in `portfolio.` and `alocação`
- it also improves future event coverage and reporting quality without entangling the core accounting ledger
