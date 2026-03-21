# OV10 Git Checkpoint Policy

Date: 2026-03-21

## Purpose

Prevent validated OV10 work from accumulating outside Git for long periods.

## Why This Exists

On 2026-03-21, OV10 had only one historical commit and 226 untracked files in the active repository surface.

That state is repository-loss risk, not normal workflow.

## Policy

### 1. No silent work outside version control

Before ending a work session, active-surface files must be in one of two states:

- intentionally tracked
- intentionally ignored

Unclassified untracked material is not an acceptable steady state.

### 2. Checkpoint cadence

Create a local checkpoint commit when:

- a coherent validated workstream is complete
- or the worktree has been dirty for more than 12 hours
- or the active repository surface has grown materially and would be costly to recreate

### 3. Push cadence

Push the current branch after a validated checkpoint when practical.

Do not let a branch remain materially ahead of upstream during long autonomous runs without an explicit reason recorded in `.codex/BACKLOG.md` or `.codex/CONTEXT.md`.

### 4. Before unattended automation

Before enabling `.codex` watchdogs, repo monitors, or other unattended continuation:

- run the Git sync audit
- confirm the worktree is intentionally classified
- confirm the checkpoint/push posture is acceptable

## Audit Command

Run the audit directly:

```powershell
.\.venv312\Scripts\python.exe .codex\scripts\git_sync_audit.py --fail-on warning
```

Write structured local audit artifacts:

```powershell
pwsh -NoLogo -NoProfile -File .codex\scripts\run_git_sync_audit.ps1
```

This writes local-only artifacts under `var\git_sync\`.

## Windows Scheduled Audit

Register a recurring local audit task:

```powershell
pwsh -NoLogo -NoProfile -File .codex\scripts\register_git_sync_audit_task.ps1
```

Default behavior:

- task name: `OV10 Git Sync Audit`
- interval: every `30` minutes
- output: `var\git_sync\git_sync_audit_latest.json`
- history: `var\git_sync\git_sync_audit_history.jsonl`

## Practical Session Close

Recommended end-of-session sequence:

1. `.\.venv312\Scripts\python.exe -m pre_commit run --all-files`
2. `.\.venv312\Scripts\python.exe .codex\scripts\git_sync_audit.py --fail-on warning`
3. `git status --short --untracked-files=all`
4. create a checkpoint commit if the slice is coherent
5. push if the checkpoint should be preserved remotely now

## Scope Note

This policy governs repository safety and synchronization discipline. It does not replace the existing language-specific quality gates.
