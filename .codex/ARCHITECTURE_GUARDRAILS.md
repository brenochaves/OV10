# ARCHITECTURE GUARDRAILS

## Guardrails

- preserve canonical IDs, batch lineage, and source traceability
- preserve the current layering:
  - `ingestion -> domain -> positions/cash/config/allocation -> services -> storage/cli`
- prefer additive or reversible changes
- do not silently alter fiscal or accounting rules
- document structural changes with an ADR under `docs/adr/`
- do not let `.codex/` overwrite stronger project truth already documented elsewhere
- do not introduce new infrastructure dependencies without a recorded reason
- do not widen scope from current local-first SQLite posture without explicit approval
- preserve the Windows-supported `.venv312` operational path unless a better verified path replaces it
