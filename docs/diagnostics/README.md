# OV10 Diagnostics

Date: 2026-03-12

This folder stores the Phase 0-A deliverables required by the handoff:

- reverse engineering of the reference workbook
- reverse engineering of the Apps Script project
- gap analysis between the current OV10 repo and the reference system
- initial benchmark of public/free corporate action sources
- multiagent execution plan for the next implementation cycles
- handoff into operational user documentation under `docs/operations/`

## Deliverables

- `2026-03-12_reverse_engineering_planilha.md`
- `2026-03-12_reverse_engineering_appsscript.md`
- `2026-03-12_gap_analysis_ov10_vs_referencia.md`
- `2026-03-12_fontes_eventos_corporativos.md`
- `2026-03-12_plano_multiagente.md`
- `2026-03-12_online_runtime_bridge.md`
- `2026-03-12_remote_payload_capture.md`
- `2026-03-12_remote_payload_function_catalog.md`
- `2026-03-19_reference_workbook_reconciliation.md`
- `2026-03-19_market_data_strategy.md`
- `2026-03-19_instrument_reference_layer.md`
- `2026-03-21_market_fx_snapshot_layer.md`

Related operational doc:

- `../operations/SETUP_AND_USAGE.md`

## Evidence Used

Local evidence:

- `data/OV10_base_2025.xlsx`
- `ov10_codex_handoff/Copia de v6.4_Controle de Investimentos (Alpha).xlsx`
- current OV10 Python scripts in repo root
- Apps Script clone pulled via `clasp` to `C:\Temp\ov10_clasp_probe`

External evidence:

- official Google Apps Script docs for `clasp` and web apps
- public DLombello pages
- public docs/portals for candidate data sources

## Notes

- The Google Apps Script project was successfully cloned with `clasp`.
- The web app URL recorded in the handoff returned `Funcao de script nao encontrada: doGet` on 2026-03-12.
- The reference Apps Script clone appears to be a thin loader/wrapper. Core business logic seems to be fetched remotely at runtime, not fully stored in the cloned project.
- The remote payload for workbook version `v6.4.02` was captured successfully as `v61_controle_64` and cataloged into domain-oriented function groups.
- A governed reference workbook reconciliation harness was added on 2026-03-19 to classify parity gaps for `portfolio.`, `caixa`, `alocação`, and `rendimentos`.
