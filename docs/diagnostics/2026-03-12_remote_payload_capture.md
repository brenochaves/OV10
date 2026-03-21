# Remote Payload Capture

Date: 2026-03-12

## Objective

Capture the JavaScript payload loaded remotely by the reference Apps Script runtime and record enough evidence to make the capture reproducible.

## Capture Result

Captured from:

- workbook spreadsheet ID: `1k4YS0jQRMzDVp34DLL8Yhb8rgM_89pGqcP-JABLRO7U`
- workbook version label: `v6.4.02`
- derived remote script version: `v61_controle_64`
- remote URL: `https://sistema.dlombelloplanilhas.com/scripts.php?key=8hfD4R5mfG&file=v61_controle_64`

Validation:

- HTTP response code: `200`
- captured payload length: `598869`
- SHA-256: `f2555392c5e045bc228873eafef0a6d218b67295f6058206809a642bdcb5cc81`

Local artifact paths:

- `var/online_runtime/reference/v61_controle_64.js`
- `var/online_runtime/reference/v61_controle_64.metadata.json`
- `var/online_runtime/reference/v61_controle_64.catalog.json`

## Important Correction

The first bridge attempt used an incorrect remote key and produced `403`.

Confirmed correct key derivation from `_Utils.js`:

- `key=8hfD4R5mfG`

The earlier truncated interpretation was wrong because the obfuscated string fragments had to be decoded after the runtime array rotation.

## Debug Copy Result

Created online debug copy:

- copied spreadsheet ID: `1DJTLhd_WWa98vrOZcRd_HhmeFV4OyD5yuS5-Mw85WBc`
- copied URL: `https://docs.google.com/spreadsheets/d/1DJTLhd_WWa98vrOZcRd_HhmeFV4OyD5yuS5-Mw85WBc/edit`

## Initial Inventory Extracted From The Payload

Observable domain modules and sheet contracts near the top of the captured script include:

- `LeiaMe`
- `Portfolio`
- `PortfolioPonto`
- `AtivosPonto`
- `Radar`
- `Rendimentos`
- `Alocacao`
- `Caixa`
- `Summary`
- `ConfigParametros`
- `ConfigOutros`
- `ConfigCarteiras`
- `ConfigBooks`
- `DARF`
- `DIRPF`
- `Extratos`
- `Historico`
- `Scripts`
- `FundamentusPonto`
- `FundsExplorerPonto`

Observed runtime constants include:

- `PLANOS_USUARIOS_ALPHA`
- `RECURSOS_USUARIOS_ALPHA`
- `CATEGORIA_SUBTOTAIS`
- `TIPO_CALCULO_OPERACOES_PROVENTOS`
- `USUARIO_ALPHA`
- `VALIDACAO_DATA_INICIO_CARTEIRA`
- `TIPO_OPERACAO_EXTRATO`

Heuristic counts from the captured file:

- total `function` declarations found: `484`
- unique function names found: `483`

## Impact

This closes the largest reverse-engineering gap identified earlier:

- the effective Apps Script runtime is no longer only inferred
- the remotely fetched business logic is now locally captured and hash-verified

The next step is no longer "find the missing logic".
The next step is "classify and map the captured runtime logic into OV10 contracts and modules".

Status update later on 2026-03-12:

- the first function catalog was generated from the captured payload
- rule clusters were separated from UI/menu and licensing logic
- the next implementation target moved to broker-attribution work informed by the `cash_brokers` cluster
