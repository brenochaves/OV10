# AGENTS

This repository uses a controlled autonomous engineering model.

## Core rule

Continue working whenever there is an executable, non-blocked task in `.codex/BACKLOG.md`.
Do not wait for human input merely because one subtask ended.

## Preservation rule

This repository may already contain professional decisions on architecture, contracts, naming, structure, CI/CD, integrations, data models, security, release flow, and operating constraints.

Before changing any of those:
1. inspect the current implementation
2. inspect `.codex/DECISIONS.md`
3. inspect `.codex/PROJECT_MEMORY_INDEX.md`
4. inspect `.codex/ARCHITECTURE_MAP.md`
5. prefer the current pattern
6. propose deviation only with explicit technical justification, expected benefit, risk analysis, and rollback feasibility

## Truth priority

1. `.codex/SYSTEM_STATE.yaml`
2. `.codex/ARCHITECTURE_GUARDRAILS.md`
3. `.codex/QUALITY_GATES.md`
4. `.codex/DECISIONS.md`
5. `.codex/PROJECT_MEMORY_INDEX.md`
6. `.codex/ARCHITECTURE_MAP.md`
7. `.codex/REPOSITORY_KNOWLEDGE_GRAPH.md`
8. `.codex/CONTEXT.md`
9. `.codex/TASK_GRAPH.md`
10. `.codex/BACKLOG.md`
11. `.codex/team/*.md`

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

## Primary roles

### Planner
- selects the next eligible task
- decomposes large tasks
- updates `.codex/TASK_GRAPH.md`
- keeps backlog grounded in repository evidence

### Coder
- implements the minimum correct change
- avoids speculative redesign
- preserves contracts unless change is explicitly justified

### Tester
- runs the smallest trustworthy validation set compatible with the stack
- records validation gaps honestly

### Reviewer
- checks architectural fit, regression risk, duplication, maintainability, and documentation impact

### Release / UAT steward
- active when mode is `uat` or `release_preparation`
- blocks non-essential drift

## Specialist roles

Specialists can be invoked when useful but must remain subordinate to repository truth and current mode.

- Architecture specialist
- Security specialist
- Performance specialist
- Bug hunter
- Test generator
- Documentation steward
- Refactor steward

See `.codex/team/` for detailed role definitions.

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

## Technical honesty

When evidence is insufficient:
- state the limitation
- record assumptions as assumptions
- do not fill gaps with invention
