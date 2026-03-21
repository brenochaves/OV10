# EXECUTION LOOP

## Selection rule

Choose the next task using this order:
1. first non-blocked `TODO` task with priority `P0`
2. first non-blocked `TODO` task with priority `P1`
3. first non-blocked `TODO` task with priority `P2`
4. first non-blocked `TODO` task with priority `P3`

If dependency rules in `.codex/TASK_GRAPH.md` prevent execution, skip to the next eligible task.

## Standard task cycle

For each selected task:
1. set task to `IN_PROGRESS`
2. identify impacted modules
3. verify relevant constraints in:
   - `.codex/ARCHITECTURE_GUARDRAILS.md`
   - `.codex/DECISIONS.md`
   - `docs/adr/`
   - `.codex/PROJECT_MEMORY_INDEX.md`
4. implement the minimum correct solution
5. run the smallest trustworthy validations
6. update docs and memory if system understanding changed
7. record the result in `.codex/AGENT_ACTIVITY_LOG.jsonl`
8. mark task `DONE`, `BLOCKED`, or `DEFERRED`
9. continue to the next eligible task

## Large-task rule

If a task is too large, ambiguous, or cross-cutting:
- do not start coding immediately
- break it into smaller verifiable tasks in `.codex/TASK_GRAPH.md`
- move implementation to the child tasks

## Backlog health rule

If fewer than 5 executable `TODO` tasks remain:
- use repository evidence to generate more small tasks
- append them to `.codex/BACKLOG.md`
- do not create speculative roadmap tasks with weak grounding

## Hard-stop conditions

Set `.codex/SYSTEM_STATE.yaml` mode to `hard_stop` and stop only when one of the following is true:
1. conflicting requirements materially affect business logic, architecture, or security
2. missing credentials or access block current and next relevant tasks
3. risk of data loss or corruption is non-trivial
4. release-critical validations fail with no safe containment path
5. required environment is broken and no safe workstream remains
6. repository state is too inconsistent to continue responsibly

## Reporting rule

When blocked:
- write exact evidence
- avoid vague statements
- classify the blockage as local or global
- propose the smallest safe next action
