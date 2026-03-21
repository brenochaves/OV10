# Remote Payload Function Catalog

Date: 2026-03-12

## Objective

Turn the captured runtime payload into a reproducible function inventory that separates:

- core business logic
- workbook update and migration logic
- UI/menu wrappers
- Alpha licensing and external-service concerns

## Artifacts

Primary runtime artifact:

- `var/online_runtime/reference/v61_controle_64.js`

Generated inventory artifact:

- `var/online_runtime/reference/v61_controle_64.catalog.json`

Generation command:

```powershell
.\.venv312\Scripts\python.exe -m ov10.cli analyze-online-remote-script var\online_runtime\reference\v61_controle_64.js
```

## Catalog Summary

Observed unique function names: `483`

Module counts from the generated catalog:

- `sheet_descriptors`: `27`
- `update_and_migration`: `83`
- `import_export_backup`: `55`
- `portfolio_positions`: `71`
- `dividends_income`: `41`
- `cash_brokers`: `27`
- `allocation_books`: `77`
- `fiscal`: `25`
- `market_data_external`: `14`
- `alpha_licensing`: `13`
- `ui_and_menu`: `27`
- `utilities`: `161`

## Main Conclusion

The captured payload is not "just calculation code".

It is a mixed runtime containing:

1. workbook contracts and sheet descriptors
2. upgrade and migration machinery
3. import/export and backup flows
4. domain logic for operations, proventos, cash, allocation, DARF, and DIRPF
5. Alpha licensing and copy-control logic
6. UI/menu wrappers and generic utilities

This matters for OV10 because it means only part of the payload is directly useful for the new backend core.

## High-Value Rule Clusters For OV10

### Portfolio, operations, and positions

Relevant evidence:

- `Portfolio`, `AtivosPonto`, and `OperacoesProventos` descriptors at lines `336`, `121`, and `209`
- `obterOperacoesProventosJSON` at line `524`
- `portfolioDefinirAtivos` at line `524`
- `portfolioOrdenarMatriz` at line `524`
- `calcularTIR` at line `2707`
- `atualizarTIR` at line `2858`

Interpretation:

- this cluster contains export/import contracts for operations and proventos
- portfolio matrix and asset routing logic are explicitly named
- TIR logic is preserved as first-class code, not only as sheet formula side effects

### Proventos and rendimentos

Relevant evidence:

- `Rendimentos` descriptor at line `278`
- `calcularProventosTotal` in the compressed runtime section that starts at line `524`
- `obterProventos`, `obterProventosV5JSON`, `executarImportacaoProventos` in the same compressed section
- `ativarRendimentos` at line `1302`

Interpretation:

- the payload has its own proventos pipeline, not only presentation helpers
- the JSON import/export names are strong clues for a portable data contract

### Cash, broker attribution, and extratos

Relevant evidence:

- `Extratos` and `Caixa` descriptors at lines `193` and `444`
- `obterCaixaJSON` at line `524`
- `importarExtratoAvenue` and `importarExtratoCEI` at line `524`
- `transferirCEICorretorasOperacoesProventos` at line `524`
- `obterTratarCorretoraInvestidor` at line `981`
- `ativarCaixa` at line `1297`

Interpretation:

- this is the most directly relevant cluster for the current OV10 warning `system_cash_account_used`
- the runtime clearly contains broker-attribution logic and transfer helpers between CEI/corretora data and operations/proventos
- this cluster should guide `TASK-102`

### Allocation, books, and carteiras

Relevant evidence:

- `Alocacao`, `Carteira`, `ConfigCarteiras`, `ConfigBooks`, and `Summary` descriptors at lines `293`, `307`, `389`, `419`, and `435`
- `obterConfigBooksJSON` and `obterConfigCarteirasJSON` at line `524`
- `ativarConfigBooks` at line `524`
- `ativarSummary` at line `1312`
- `definirPadraoConfigCarteiras` at line `2131`
- `definirPadraoConfigBooks` at line `2591`
- `definirPadraoSummary` at line `2645`
- `definirPadraoAlocacao` at line `2651`

Interpretation:

- allocation and book logic are significant runtime concerns, not cosmetic worksheet setup
- the existing OV10 config adapter should continue to map toward these contracts instead of inventing a new vocabulary

### Fiscal

Relevant evidence:

- `DARF` and `DIRPF` descriptors at lines `465` and `474`
- `calcularDARF` and `calcularDIRPF` in the compressed runtime section that starts at line `524`
- `executarCalcularDARF` and `executarCalcularDIRPF` in the same section
- `definirPadraoDARFDIRPF` at line `2580`

Interpretation:

- DARF and DIRPF are explicit modules with their own entrypoints and layout logic
- OV10 should keep the current contract-first fiscal plan, but now with stronger evidence that these outputs are runtime-backed modules

## Lower-Value Sections For OV10 Core Porting

### Update and migration

Examples:

- `verificarAtualizacoes`
- `atualizarVersao`
- `executarAtualizacaoAbas`
- `atualizarAba`

Observation:

- these functions are important to understand the spreadsheet product lifecycle
- they are lower-value for the accounting engine itself

### UI and menu wrappers

Examples:

- `html_main`
- `html_alpha`
- `html_books`
- `mensagemUsuario`
- `obterConfirmacaoUsuarioYESNO`

Observation:

- this layer explains user flows and feature discoverability
- it should not be confused with core accounting logic

### Licensing and Alpha copy control

Relevant evidence:

- `PLANOS_USUARIOS_ALPHA` at line `45`
- `RECURSOS_USUARIOS_ALPHA` at line `62`
- `validarIDPlanilha` at line `981`
- `validarRecursoUsuarioAlpha` at line `981`

Observation:

- this is real runtime logic, but it is product-enforcement logic rather than portfolio-accounting logic
- OV10 should treat it as out of scope for core financial behavior

## External Integrations Seen In The Payload

Relevant evidence:

- `FundamentusPonto` at line `175`
- `getStockinfoApi` at line `981`
- `atualizarIndicadores` at line `981`
- `exportarYahoo` at line `3229`
- `fundamentus` marker at line `177`

Interpretation:

- the runtime depends on external market-data sources in addition to Google Sheets formulas
- some workbook behavior is therefore sensitive not only to sheet formulas but also to remote HTTP integrations

## Important Caveat About References

The captured payload contains compressed sections.

As a result:

- several high-value functions resolve to the same source line, especially `524` and `981`
- this does not mean they are the same function
- it means those functions live inside consolidated runtime blocks in the captured artifact

For reproducible analysis, use the generated JSON catalog together with the payload file.

## OV10 Impact

This catalog is enough to set the next technical direction with less guesswork:

- `TASK-111` is satisfied
- `TASK-102` should now mine the `cash_brokers` cluster for broker-attribution rules
- fiscal work should stay contract-first, but now with concrete DARF/DIRPF runtime evidence
- Alpha licensing should remain explicitly outside the OV10 accounting core
