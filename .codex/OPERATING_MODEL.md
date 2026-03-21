# OPERATING MODEL

## Objective

Provide a professional autonomous execution loop for OV10 with:

- repository-first execution
- durable memory
- explicit state
- quality gates grounded in the actual stack
- specialist review paths
- reversible changes

## Canonical loop

1. read `.codex/SYSTEM_STATE.yaml`
2. read `.codex/CONTEXT.md`
3. read `.codex/DECISIONS.md`
4. read `.codex/ARCHITECTURE_GUARDRAILS.md`
5. read `.codex/QUALITY_GATES.md`
6. inspect repository sync posture with `git status` or `.codex/scripts/git_sync_audit.py` when the worktree is materially dirty or a long session is underway
7. inspect `.codex/BACKLOG.md`
8. select the next eligible task
9. if large or ambiguous, decompose into `.codex/TASK_GRAPH.md`
10. implement the minimum correct change
11. validate
12. checkpoint repository state when the workstream is coherent and validated
13. update memory and logs
14. continue

## Modes

- `integration_analysis`
- `memory_build`
- `development`
- `stabilization`
- `uat`
- `release_preparation`
- `hard_stop`

## Long-running stability model

This repository may be worked in long sessions. To reduce context loss:

- keep concise state in `.codex/memory/context_summary.md`
- snapshot richer state in `.codex/memory/context_snapshot.md`
- keep `.codex/AGENT_ACTIVITY_LOG.jsonl` append-only
- prefer small tasks with explicit acceptance
- rotate context periodically with `.codex/scripts/context_rotator.py`
- avoid leaving large untracked surfaces or long-lived dirty worktrees without an explicit checkpoint plan

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
