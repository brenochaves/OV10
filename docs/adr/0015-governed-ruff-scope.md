# ADR 0015: Governed Ruff Scope

Date: 2026-03-21

## Status

Accepted

## Context

By 2026-03-21, the OV10 repository had a healthy governed surface under:

- `src/ov10/`
- `tests/`
- `.codex/scripts/`

That surface was already lint-clean.

At the same time, `ruff check .` still failed because the repository also contains:

- legacy exploratory root-level scripts:
  - `main.py`
  - `leitor_planilha.py`
  - `consolidar_posicao.py`
  - `exportador.py`
- archived scaffolding snapshots under `archive/`

Some of those failures were only style issues, but others were real parse failures in non-governed files.

Leaving the scope ambiguous weakens the quality signal:

- green lint on the supported surface already exists
- repo-wide lint stays noisy for reasons unrelated to the current OV10 core

## Decision

Keep `ruff` as a required quality layer, but govern its scope explicitly.

The supported `ruff` scope for OV10 is:

- all Python files under `src/`
- all Python files under `tests/`
- all Python files under `.codex/scripts/`

The following files/directories are excluded from the default `ruff` policy:

- `archive/`
- `main.py`
- `leitor_planilha.py`
- `consolidar_posicao.py`
- `exportador.py`

This is implemented in `pyproject.toml` through `extend-exclude` and `force-exclude`, so:

- `ruff check .` becomes a stable governed check
- direct path invocation still respects the exclusion policy

## Consequences

Positive:

- `ruff` becomes a reliable quality gate again.
- VS Code tasks can continue to run `ruff check .` without false repository-wide noise.
- The governed OV10 surface gains another robust validation layer without forcing immediate refactoring of legacy material.

Tradeoffs:

- The excluded legacy files are still not lint-clean.
- This decision does not rehabilitate those files; it only classifies them as out of the supported quality envelope.

## Follow-up

- If any excluded file is promoted into the governed OV10 path, remove the exclusion and bring it under the standard quality gates.
- CI should use the same governed `ruff` invocation as the local operator path.
