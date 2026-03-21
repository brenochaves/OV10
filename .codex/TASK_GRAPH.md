# TASK GRAPH

## Active Chain

1. `TASK-101`
   - completed: import workbook configuration into current OV10 contracts
2. `TASK-102`
   - improve corporate action broker attribution using the richer config and source context
3. `TASK-103`
   - compare OV10 outputs against selected reference workbook outputs
4. `TASK-105`
   - define fiscal contracts once reconciliation boundaries are clearer

## Parallelizable Work

- `TASK-106`
  - CI setup can proceed independently from the workbook-config adapter

- `TASK-107`
  - operator documentation can improve in parallel as long as it only documents shipped behavior

- `TASK-104`
  - instrument reference normalization can start after the config adapter contracts are clear

- `TASK-108`
  - completed: local synthetic workbook generation is available for perturbation testing

## Blockers And Dependencies

- `TASK-102` depends on `TASK-101` because broker attribution benefits from richer workbook configuration context
- `TASK-103` depends on `TASK-101` because reference-aligned configuration is needed before deeper parity claims
- `TASK-105` depends on `TASK-103` because fiscal contracts should align with a more stable accounting baseline

## Completion Rule

A task is only considered done when:

- code or documentation is committed in the repo
- tests or equivalent validation evidence exist
- ADR updates exist for structural decisions
- `.codex/CONTEXT.md` and `.codex/DECISIONS.md` stay consistent with the change
