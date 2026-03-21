# BACKLOG

## TASK-001
status: TODO
priority: P0
type: integration
summary: Inspect repository structure, stack, conventions, and existing engineering decisions.
acceptance:
- repository map captured
- key conventions identified
- major risks listed

dependencies: none
notes: Start here during integration_analysis.

## TASK-002
status: TODO
priority: P0
type: memory
summary: Populate project memory files from repository evidence.
acceptance:
- PROJECT_MEMORY_INDEX updated
- ARCHITECTURE_MAP updated
- REPOSITORY_KNOWLEDGE_GRAPH updated

dependencies: TASK-001
notes: Must reflect facts only.

## TASK-003
status: TODO
priority: P1
type: backlog
summary: Replace generic backlog items with real project tasks grounded in repository evidence.
acceptance:
- generic placeholders removed or deprioritized
- at least 5 executable tasks created

dependencies: TASK-002
notes: Preserve release and architecture constraints.

## TASK-004
status: TODO
priority: P2
type: docs
summary: Update context and decision records after kit adaptation.
acceptance:
- CONTEXT updated
- DECISIONS updated
- activity log entry added

dependencies: TASK-002
notes: Keep concise.
