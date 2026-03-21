# OV10 Apps Script Debug Bridge

Date: 2026-03-12

This standalone Apps Script project is the online-first bridge for reverse engineering the live Google Sheets runtime.

Current project identifiers:

- script ID: `1VUJIED8fKZJmU62TSENsDG8IiXS8RNc5OutC97A8Jsjr6coHON1uhGdp`
- editor URL: `https://script.google.com/d/1VUJIED8fKZJmU62TSENsDG8IiXS8RNc5OutC97A8Jsjr6coHON1uhGdp/edit`
- current versioned deployment: `AKfycbyyV_nNLy3jaTyBwZmEdFvyOR9JGjNk1Z_EFM1-WnNNi0s5RxWQI2EacyV285N_DCzU`
- current web app URL: `https://script.google.com/macros/s/AKfycbyyV_nNLy3jaTyBwZmEdFvyOR9JGjNk1Z_EFM1-WnNNi0s5RxWQI2EacyV285N_DCzU/exec`

## Why this exists

- the exported `.xlsx` is structurally useful but not runtime-faithful
- the cloned bound Apps Script is only part of the system
- `_Utils.js` fetches remote JavaScript from `sistema.dlombelloplanilhas.com` and executes it with `eval(...)`
- this bridge lets OV10 inspect the live sheet and capture that remote payload without editing the original production script first

## Current scope

- list sheets and named ranges
- preview or read selected ranges with values and formulas
- derive the workbook version from `LeiaMe!B6`
- reconstruct the remote script URL used by the original loader
- fetch the remote payload summary or chunked content
- create a debug copy of the spreadsheet for safe bound-script instrumentation later
- inspect protections and the bridge's own triggers/properties

## Deployment commands

Push the project:

```powershell
cmd /c clasp push
```

Create a version:

```powershell
cmd /c clasp version "OV10 debug bridge initial instrumentation"
```

Create a deployment:

```powershell
cmd /c clasp deploy -d "OV10 Debug Bridge"
```

Open the Apps Script project:

```powershell
cmd /c clasp open
```

## Main functions

- `dbgPing()`
- `dbgListSheets(spreadsheetId)`
- `dbgListNamedRanges(spreadsheetId)`
- `dbgReadRange(spreadsheetId, sheetName, a1Notation)`
- `dbgSheetPreview(spreadsheetId, sheetName, maxRows, maxColumns)`
- `dbgWorkbookVersion(spreadsheetId)`
- `dbgFetchRemoteScriptSummary(spreadsheetId)`
- `dbgFetchRemoteScriptChunk(spreadsheetId, start, length)`
- `dbgCreateDebugCopy(sourceSpreadsheetId, copyNamePrefix)`
- `dbgDescribeProtections(spreadsheetId)`
- `dbgBridgeState()`

The bridge also exposes `doGet` and `doPost` with a small JSON dispatch layer, so the same operations can later be exercised through a web-app deployment if needed.

## Operational notes

- the current web-app deployment uses an explicit `bridgeKey` gate for HTTP access
- the bridge was validated against the live workbook version `v6.4.02`
- the remote runtime payload `v61_controle_64` was captured successfully through this bridge on 2026-03-12

## Likely one-time authorization prompt

Because the bridge uses:

- `SpreadsheetApp`
- `DriveApp`
- `UrlFetchApp`

Google may ask for a one-time authorization when the project is first executed. If that happens, open the script in the browser, run `dbgPing`, and approve the requested scopes.
