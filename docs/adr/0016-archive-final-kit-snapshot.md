# ADR 0016: Archive Final Kit Snapshot

Date: 2026-03-21

## Status

Accepted

## Context

The repository originally received a `final_kit/` directory as a generic autonomy scaffold.

OV10 then selectively adopted the useful parts of that material into the active root `.codex/` control plane, as documented in ADR 0007. By 2026-03-21:

- `.codex/` already contained the active backlog, state, prompts, specialist roles, and scripts
- OV10-specific rules had replaced the generic placeholder content
- `final_kit/` no longer provided active runtime value to the governed repository surface

Keeping `final_kit/` at the root created two avoidable problems:

- it looked more active than it really was
- it polluted repository-wide quality and maintenance boundaries even though it had already been superseded

## Decision

Retire `final_kit/` as an active repository surface and archive it under:

- `archive/final_kit_2026-03-12/`

This archived snapshot is kept only for provenance and historical comparison.

Rules after archiving:

- the active autonomy/control framework is root `.codex/`
- archived material under `archive/` is not part of the supported runtime, lint, or operator surface
- future work must not use the archived kit as a higher-trust source than current OV10 code, tests, ADRs, diagnostics, operations docs, or root `.codex/`

## Consequences

Positive:

- the repository root now reflects the real active architecture
- historical provenance is preserved without pretending the archived kit is still active
- quality gates can stay focused on supported code and control-plane assets

Tradeoffs:

- anyone inspecting old ADRs will still see historical references to `final_kit/`
- the archived snapshot remains in the repo and still consumes versioned space

## Follow-up

- keep `archive/` excluded from the governed lint surface
- treat ADR 0007 as historical adoption rationale and ADR 0016 as the retirement/archive step
