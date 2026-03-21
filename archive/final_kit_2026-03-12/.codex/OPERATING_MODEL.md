# OPERATING MODEL

## Objective

Provide a professional autonomous execution loop for Codex in an existing repository with controlled risk, explicit memory, long-running stability, specialist review paths, and auditable state transitions.

## Principles

- repository-first execution
- explicit state
- durable memory
- quality gates
- guardrails
- reversible changes
- evidence-based backlog generation
- human supervision only at meaningful boundaries

## Canonical loop

1. read `.codex/SYSTEM_STATE.yaml`
2. read `.codex/CONTEXT.md`
3. read `.codex/DECISIONS.md`
4. read `.codex/ARCHITECTURE_GUARDRAILS.md`
5. read `.codex/QUALITY_GATES.md`
6. inspect `.codex/BACKLOG.md`
7. select the next eligible task
8. if large or ambiguous, decompose into `.codex/TASK_GRAPH.md`
9. implement the minimum correct change
10. validate
11. update memory and logs
12. continue

## Modes

- `integration_analysis`
- `memory_build`
- `development`
- `stabilization`
- `uat`
- `release_preparation`
- `hard_stop`

## Long-running stability model

This kit assumes that long sessions may lose context or stop unexpectedly. To mitigate that:
- maintain concise state in `.codex/memory/context_summary.md`
- snapshot important state in `.codex/memory/context_snapshot.md`
- keep logs append-only and compact
- prefer small tasks
- periodically rotate context using `scripts/context_rotator.py`

## Stop philosophy

### Local blockage
If only one task is blocked:
- mark it `BLOCKED`
- record exact evidence
- continue to the next eligible task

### Hard stop
Use `hard_stop` only if the issue:
- threatens data integrity
- threatens security
- threatens release viability
- requires unavailable credentials or external access
- invalidates multiple queued tasks
- reveals contradictory requirements with architectural impact
- leaves no safe executable workstream
