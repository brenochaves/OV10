# Reverse Engineering - Apps Script Reference

Date: 2026-03-12

## Access Validation

Actions executed:

- validated local `clasp` installation
- cloned script ID `12-A3Ve0u1nlhI_3cKBj454LsA7aZRp2i0lOlj4Czu8QhSUgMoOy66uDz`
- inspected cloned files
- tested the web app URL recorded in handoff

Result:

- `clasp clone` worked
- handoff `exec` URL returned `Funcao de script nao encontrada: doGet`
- `clasp deployments` showed `AKfycbyLG70N81tg5iIYamtyPorydvyJN49qauRHnosQUA @HEAD`
- the recorded deployment and live behavior are not enough to treat the web app as a stable inspection API

## Cloned File Inventory

Clone path used during analysis:

- `C:\Temp\ov10_clasp_probe`

| File | Type | Role | Portability | Notes |
|---|---|---|---|---|
| `appsscript.json` | manifest | scopes/runtime/services | partial | useful for access model |
| `_Menu.js` | wrapper | menu entrypoints for operations | partial | useful for feature inventory |
| `_OnOpen.js` | wrapper/UI | custom menu and generic transmitter | partial | useful for orchestration only |
| `_Utils.js` | loader/infra | script versioning, cache, remote fetch, error handling | high insight, low direct reuse | key architectural discovery |
| `_regex.js` | utility | HTML regex extraction helper | low | generic helper only |
| `_JSON.js` | third-party lib | ImportJSON library | low | useful as evidence of JSON import patterns, not core domain logic |
| `_moment.min.js` | third-party lib | moment.js | low | generic date helper only, replaced by native/Python tooling in OV10 |

## Key Finding: Thin Local Wrapper, Remote Runtime Logic

The most important discovery is in `_Utils.js`.

Observed behavior:

- resolves a `script_version()`
- reads workbook version from `LeiaMe!B6`
- builds a remote URL
- fetches remote script content
- caches fetched content in chunks
- executes remote payload via `eval(obterScript())`

Implication:

- the cloned Apps Script project does not contain the full business logic
- the local clone is an orchestrator/loader shell
- a large portion of the effective runtime behavior likely lives in remotely served code

## Clarification: What "Local" Means Here

In this document, "local" means the `clasp` clone on disk:

- `C:\Temp\ov10_clasp_probe`

Important clarification:

- the online Apps Script editor and the `clasp` clone refer to the same Apps Script project
- `clasp` can only download the files that are actually stored inside that Apps Script project
- it cannot download code that the project fetches later from an external server during execution

Therefore:

- the missing logic is not "hidden somewhere else inside the same Apps Script editor"
- it is genuinely external to the Apps Script project as stored in Google
- `_Utils.js` proves this by building a remote URL and executing the returned payload with `eval(...)`

## Where The Business Logic Is Proven To Be

Based on evidence collected on 2026-03-12, the reference system's business logic is split across:

1. workbook formulas and sheet structure
   - strong evidence in `portfolio`, `rendimentos`, `caixa`, `alocacao`, `config.books`, `portfolio.`, `ativos.`, `darf`, and `dirpf`
2. Apps Script wrapper/orchestration
   - menus, triggers, version routing, cache, and remote script loading
3. remotely fetched script payload
   - `_Utils.js` fetches versioned code from an external server and executes it with `eval`

What is not yet fully captured:

- the contents of the remote payload loaded by `obterScript()`

This means the current reverse engineering baseline already contains real business logic from the workbook itself, but the script-side logic is only partially captured until the remote payload is obtained from a controlled copy or from an API-enabled execution path.

Status update later on 2026-03-12:

- the standalone bridge was authorized and redeployed
- the remote key was decoded correctly as `8hfD4R5mfG`
- the payload for `v61_controle_64` was captured successfully with HTTP `200`
- the capture was saved locally and hash-verified
- the payload was cataloged into domain-oriented function groups for positions, dividends, cash, allocation, fiscal, licensing, UI, and migration logic

This closes the earlier raw-retrieval gap for the observed workbook version. What remains is structured analysis, not payload access.

## Online-First Bridge Status

To close this gap, OV10 now has a standalone Apps Script debug bridge under:

- `apps_script_debug_bridge/`

Current status on 2026-03-12:

- standalone bridge project created successfully
- `clasp push` succeeded
- deployment succeeded with both `WEB_APP` and `EXECUTION_API` entry points
- direct `clasp run` still returned `The caller does not have permission`
- the web app deployment is currently restricted to `MYSELF`, so direct HTTP requests without a logged-in browser session land on the Google sign-in page

Interpretation:

- bridge infrastructure now exists
- the likely remaining blocker is one-time Google authorization and/or execution-path permissions
- this is a much narrower problem than the earlier uncertainty about where the runtime logic lives

Follow-up outcome:

- the authorization step was completed
- a web-app path with explicit `bridgeKey` gating was used successfully
- a debug copy of the workbook was created
- the remote runtime payload was retrieved through the bridge

## Why `_JSON.js` and `_moment.min.js` Were Not Treated As Core Assets

Reason:

- they are generic support libraries, not portfolio-accounting rules
- `_JSON.js` is a reusable import helper and does not encode OV10-specific accounting behavior
- `_moment.min.js` is a generic date library and does not encode portfolio, tax, dividend, or corporate action rules

Conclusion:

- they may still be useful as implementation references if OV10 ever needs analogous utilities
- they do not materially reduce the domain-modeling work required for OV10

## Functional Inventory from Menu Layer

Entrypoints found in `_Menu.js` / `_OnOpen.js` include:

- calculate operations
- calculate dividends
- calculate operations + dividends
- update indicators
- update asset fundamentals
- update assets / TIR
- calculate DARF
- calculate and update everything
- disable sheet processing
- check updates
- help

These wrappers are useful to infer major feature domains, but they do not implement the rules themselves.

## What Is Reusable

Reusable insights:

- feature inventory
- orchestration topology
- cache/version pattern
- evidence that workbook version and runtime script version are linked

Not directly reusable:

- local wrapper code as domain engine
- web app endpoint as integration contract
- dynamic remote eval pattern

## Risks

- the true business logic is partially outside the cloned artifact
- remote code may change independently from the workbook clone
- any attempt to port rules only from local Apps Script files would be incomplete

## OV10 Impact

For OV10, the spreadsheet remains the stronger source of truth for reverse engineering than the Apps Script clone alone.

Important boundary:

- the offline `.xlsx` export is not enough to claim equivalence with the online Google Sheets runtime
- the online reference behavior depends on workbook formulas, Apps Script orchestration, and remotely fetched script payload
- the exported `.xlsx` loses part of that execution environment by definition

Therefore, the current reference hierarchy should be:

1. online Google Sheets behavior, when observable
2. workbook structure and formulas as reverse-engineering evidence
3. Apps Script clone as orchestration and remote-loader evidence
4. offline `.xlsx` export as a structural artifact, not a full runtime twin

Recommended use of the Apps Script findings:

- confirm system modules
- confirm workflow names and user actions
- confirm that versioned remote logic exists
- avoid overestimating how much rule logic can be extracted from the local clone
