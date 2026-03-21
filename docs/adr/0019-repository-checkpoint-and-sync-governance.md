# ADR 0019: Repository Checkpoint And Sync Governance

Date: 2026-03-21

## Status

Accepted

## Context

OV10 accumulated a large amount of validated engineering work without corresponding Git checkpoints.

On 2026-03-21, the repository still had:

- a single historical commit on `main`
- only 7 tracked files
- 226 untracked files in the active repository surface
- no local divergence from `origin/main` only because the new work had never been committed

This is a repository-loss risk, not just a cosmetic hygiene issue.

## Decision

OV10 adopts an explicit Git checkpoint and remote-sync governance layer:

1. Repository hygiene becomes part of the active control plane.
2. A governed audit script reports tracked/untracked counts, dirty-state age, and upstream divergence.
3. Long-lived dirty worktrees and large untracked surfaces are treated as repository-governance failures.
4. Each coherent validated workstream should end in a local checkpoint commit.
5. Local commits should not remain unpushed for long-running autonomous work without explicit justification.
6. Windows task-scheduler automation is provided as an opt-in local reminder/audit path.

## Consequences

Positive:

- repository-loss risk becomes visible and measurable
- autonomous work is less likely to accumulate outside Git
- operator and agent behavior align around a concrete checkpoint cadence

Negative:

- local process becomes stricter
- repository governance adds one more operational discipline to maintain
- scheduled auditing can produce noise if the repo is intentionally left dirty for short experiments

## Scope Notes

- This ADR governs checkpoint cadence and sync visibility, not secret handling or broader security hardening.
- It does not authorize destructive Git commands or automatic pushes.
- It complements, but does not replace, the existing quality gates and backlog discipline.
