# ADR 0010: Use A Standalone Apps Script Debug Bridge For Online Runtime Reverse Engineering

Date: 2026-03-12

## Status

Accepted

## Context

OV10 needs high-confidence reverse engineering of the reference system.

New evidence confirmed that:

- the exported `.xlsx` is not a runtime-faithful twin of the online sheet
- the cloned Apps Script project is only a loader/orchestration shell
- `_Utils.js` fetches remote JavaScript and executes it with `eval(...)`

That means the remaining uncertainty is concentrated in the online runtime and in the remotely loaded payload.

## Decision

Adopt an online-first reverse engineering bridge using a standalone Apps Script project under `apps_script_debug_bridge/`.

Rules:

- do not treat the offline `.xlsx` as executable reference behavior
- use the standalone bridge to inspect the live workbook by ID
- capture the remote script URL and payload derived from `LeiaMe!B6`
- create and use a debug copy before any bound-script instrumentation
- keep the bridge versioned in the OV10 repo, with explicit scopes and runbook instructions

## Consequences

- OV10 now has a governed path to inspect the real online runtime
- the main remaining blocker is reduced to Google execution authorization instead of architectural uncertainty
- the offline export remains useful as structural evidence, but not as authoritative runtime behavior
- bound-script instrumentation remains a second-stage option, to be used on a copied spreadsheet only

Status update on 2026-03-12:

- the bridge path was validated end to end
- a debug copy was created
- the remote payload for `v61_controle_64` was captured and hash-verified
