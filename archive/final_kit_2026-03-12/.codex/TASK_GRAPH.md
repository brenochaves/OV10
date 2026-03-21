# TASK GRAPH

Use this file when a task must be decomposed into smaller child tasks.

## Example

- TASK-100 parent
  - TASK-100A child
  - TASK-100B child
  - TASK-100C child

Rules:
- child tasks must be independently verifiable
- dependencies must be explicit
- parent task should not move to DONE until required children are DONE or intentionally DEFERRED with justification
