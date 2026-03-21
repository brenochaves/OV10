# ADR 0011: Corporate Action Cash Broker Attribution

Date: 2026-03-12

## Status

Accepted

## Context

OV10 persisted corporate action cash components into the system account whenever the source workbook did not explicitly provide a broker name for the event.

This created a visible reconciliation warning in the current fixture:

- `system_cash_account_used`

After capturing and classifying the live Apps Script runtime, the `cash_brokers` cluster showed concrete evidence that the reference system has broker-routing logic around:

- `transferirCEICorretorasOperacoesProventos`
- `obterTratarCorretoraInvestidor`
- `importarExtratoCEI`
- `obterCaixaJSON`

That evidence justified implementing a governed attribution heuristic in the OV10 backend instead of treating every corporate action cash row as permanently unassigned.

## Decision

For corporate action cash movements, OV10 now applies the following broker-attribution policy:

1. if multiple historical brokers held the source instrument before the event date, keep the cash in the system account and classify the case as ambiguous
2. else if the same event date has a unique conversion broker across `CONVERSION_OUT` / `CONVERSION_IN` transactions tied to the source or target instrument, assign the cash to that broker
3. else if there is a unique historical broker holding the source instrument before the event date, assign the cash to that broker
4. else keep the cash in the system account and classify the case as no-candidate

Reconciliation now distinguishes unresolved cases explicitly:

- `system_cash_account_used_ambiguous`
- `system_cash_account_used_no_candidate`

## Consequences

Positive:

- the current real fixture no longer needs a system account for the single cash-bearing corporate action
- the broker-assigned cash balance now lands in `INTER DTVM LTDA`
- unresolved cases remain visible and classified instead of being silently forced into a broker
- synthetic tests now cover both attributed and unattributed paths

Tradeoffs:

- this is still a heuristic, not a guaranteed reproduction of every private spreadsheet rule
- multi-broker corporate actions may remain unresolved until stronger evidence is extracted
- the backend still does not split one corporate action cash component across multiple brokers

## Evidence

- captured runtime payload catalog: `docs/diagnostics/2026-03-12_remote_payload_function_catalog.md`
- captured payload artifact: `var/online_runtime/reference/v61_controle_64.js`
- generated catalog artifact: `var/online_runtime/reference/v61_controle_64.catalog.json`
