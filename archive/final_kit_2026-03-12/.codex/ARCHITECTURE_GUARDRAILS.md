# ARCHITECTURE GUARDRAILS

These guardrails are intentionally conservative until the repository is inspected.

## Guardrails

- preserve existing public contracts unless change is justified and documented
- avoid broad refactors during active delivery or stabilization pressure
- prefer additive or reversible changes
- do not move files or rename modules solely for aesthetics
- preserve current CI/CD expectations unless there is an approved reason to change them
- do not change data models, migrations, auth, or permissions casually
- do not introduce new infrastructure dependencies without a clear recorded reason
