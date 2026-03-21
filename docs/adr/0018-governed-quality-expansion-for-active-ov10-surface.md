# ADR 0018: Governed Quality Expansion For Active OV10 Surface

Date: 2026-03-21

## Status

Accepted

## Context

After the first multi-stack lint baseline, OV10 still lacked five approved layers for the active repository surface:

- Python type checking
- explicit TOML and structured JSON validation
- governed SQL linting
- software-composition analysis for Python and Node
- local `pre-commit` orchestration

The project goal is to improve robustness without broadening governance to archived or legacy material.

## Decision

OV10 expands the governed quality baseline as follows:

1. Python type checking uses `pyright` and is scoped initially to `src/ov10`.
2. Active TOML config and selected structured JSON payloads are validated explicitly in code before use.
3. Governed SQL lives under `sql/`, with `sqlfluff` applied to that surface using the SQLite dialect.
4. Dependency auditing uses `pip-audit` for Python and `npm audit` for Node.
5. `.pre-commit-config.yaml` is added as a local orchestrator, delegating to the same governed commands already documented for operators and CI.

## Consequences

Positive:

- type drift in contracts and adapters is surfaced earlier
- config and runtime payload failures become more actionable
- SQL becomes a first-class governable artifact rather than an opaque embedded string
- dependency risk has an explicit reproducible audit path
- local commits can run the governed baseline without inventing a second policy

Negative:

- setup cost increases slightly due to extra tooling
- CI becomes broader and somewhat slower
- SQL schema maintenance now requires keeping the external `sql/` artifact aligned with runtime behavior

## Scope Notes

- The governed scope remains intentionally limited to the active OV10 surface.
- `archive/` and legacy exploratory root scripts remain outside this quality envelope.
- Security hardening of the dev bridge stays deferred under the separate post-MVP decision path.
