# AGENTS

This repository uses a controlled autonomous engineering model.

## Core rule

Continue working whenever there is an executable, non-blocked task in `.codex/BACKLOG.md`.
Do not wait for human input merely because one subtask ended.

## Preservation rule

This repository already contains material engineering decisions in code and documentation.

Before changing architecture, contracts, data models, operator flow, or project structure:
1. inspect the current implementation
2. inspect `docs/adr/`
3. inspect `docs/diagnostics/`
4. inspect `docs/operations/`
5. inspect `.codex/DECISIONS.md`
6. inspect `.codex/PROJECT_MEMORY_INDEX.md`
7. prefer the current OV10 pattern
8. propose deviation only with explicit technical justification, expected benefit, risk analysis, and rollback feasibility

## Truth priority

1. executable code under `src/ov10/`
2. tests under `tests/`
3. `docs/adr/`
4. `docs/diagnostics/`
5. `docs/operations/`
6. `.codex/SYSTEM_STATE.yaml`
7. `.codex/ARCHITECTURE_GUARDRAILS.md`
8. `.codex/QUALITY_GATES.md`
9. `.codex/DECISIONS.md`
10. `.codex/PROJECT_MEMORY_INDEX.md`
11. `.codex/ARCHITECTURE_MAP.md`
12. `.codex/REPOSITORY_KNOWLEDGE_GRAPH.md`
13. `.codex/CONTEXT.md`
14. `.codex/TASK_GRAPH.md`
15. `.codex/BACKLOG.md`
16. `.codex/team/*.md`

## Task statuses

- TODO
- IN_PROGRESS
- BLOCKED
- DONE
- DEFERRED

## Priorities

- P0
- P1
- P2
- P3

## Allowed autonomy

The agent may:
- plan
- implement
- test
- update docs and memory files
- generate grounded backlog items
- mark tasks `BLOCKED`
- continue to the next eligible task
- create small child tasks in `.codex/TASK_GRAPH.md`

The agent must stop only for `hard_stop` conditions defined in `.codex/EXECUTION_LOOP.md`.

## Repository hygiene rule

- do not allow validated active-surface work to accumulate outside Git for long periods
- classify active files as tracked or ignored before ending a work session
- run `.codex/scripts/git_sync_audit.py` when repository-loss risk is non-trivial
- prefer a checkpoint commit after a coherent validated slice instead of carrying large dirty state indefinitely
- record explicit reasons in `.codex/BACKLOG.md` or `.codex/CONTEXT.md` if local commits must remain unpushed for a while

## Subagent discipline

Subagents exist to reduce latency or isolate a bounded responsibility, not to "think twice" about the same question.

Rules:

- do not send two agents to inspect the same artifact with the same goal
- only delegate when the subtask is materially disjoint from the main rollout
- prefer one explorer for runtime/reference evidence and one explorer for local integration impact
- if two agents touch the same topic, their prompts must differ by ownership, artifact set, or output contract
- if overlap is discovered, stop spawning and collapse the work back into the main rollout
- close idle agents when their assigned slice is complete

Recommended split for this repo:

- runtime/reference explorer: captured payload, workbook semantics, external-source evidence
- codebase explorer: current OV10 modules, insertion points, test surface, migration impact
- worker: bounded implementation with explicit file ownership

## Technical honesty

When evidence is insufficient:
- state the limitation
- record assumptions as assumptions
- do not fill gaps with invention
