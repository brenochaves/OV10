# Online Runtime Bridge

Date: 2026-03-12

## Objective

Capture and inspect the real Google Sheets + Apps Script runtime without pretending that the exported `.xlsx` is an executable twin.

## Why this path was chosen

Observed evidence:

- the offline export contains many degraded formulas such as `__xludf.DUMMYFUNCTION(...)`
- the reference Apps Script clone loads remote JavaScript from `sistema.dlombelloplanilhas.com` and executes it with `eval(...)`

Therefore:

- reverse engineering based only on the offline export is incomplete
- reverse engineering based only on the `clasp` clone is also incomplete
- the correct target is the online runtime plus the remotely fetched payload

## Bridge Architecture

Standalone Apps Script project:

- script ID: `1VUJIED8fKZJmU62TSENsDG8IiXS8RNc5OutC97A8Jsjr6coHON1uhGdp`
- editor URL: `https://script.google.com/d/1VUJIED8fKZJmU62TSENsDG8IiXS8RNc5OutC97A8Jsjr6coHON1uhGdp/edit`
- repo path: `apps_script_debug_bridge/`

Current bridge capabilities:

- inspect sheet inventory and named ranges
- preview or read selected ranges
- derive workbook version from `LeiaMe!B6`
- reconstruct the remote script URL used by `_Utils.js`
- fetch the remote script summary or chunked content
- create a debug copy of the spreadsheet
- inspect protections
- expose both callable functions and `doGet` / `doPost`

## Deployment Evidence

Validated on 2026-03-12:

- `clasp push -f` succeeded
- `clasp deploy -d "OV10 Debug Bridge - fixed remote key"` succeeded
- deployment `AKfycbyyV_nNLy3jaTyBwZmEdFvyOR9JGjNk1Z_EFM1-WnNNi0s5RxWQI2EacyV285N_DCzU` was created
- Google Apps Script API confirmed two entry points:
  - `WEB_APP`
  - `EXECUTION_API`

Current behavior:

- `clasp run dbgPing` returned permission denial
- direct HTTP to the web app now works through explicit `bridgeKey` gating
- debug copy creation and remote payload fetch were both validated through that web path

## Current Interpretation

The uncertainty has narrowed down to execution authorization, not to architecture.

What is already solved:

- where to instrument
- how to derive the remote script URL
- how to fetch payload once the bridge is allowed to execute
- how to create a safe debug copy instead of touching production first

What remains:

- structured analysis of the captured runtime payload
- targeted mining of the broker-attribution and fiscal rule clusters

## Recommended Next Step

Run `dbgPing()` once in the browser editor for the standalone bridge and approve the requested scopes.

After that, retest:

- `clasp run dbgPing`
- `dbgCreateDebugCopy()`
- `dbgFetchRemoteScriptSummary()`

## Status Update

The authorization step was completed later on 2026-03-12.

Follow-up result:

- the bridge was redeployed with explicit `bridgeKey` gating
- a debug copy of the workbook was created successfully
- the remote payload was fetched successfully
- a first function catalog was generated from the captured runtime

Next frontier:

- analyze and catalog the captured runtime logic rather than only proving that it exists
