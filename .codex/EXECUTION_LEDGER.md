# Execution Ledger

Date: 2026-03-21

Purpose:

- separate what is already executed from what is only approved
- keep conversation decisions anchored in repository artifacts
- avoid losing accepted workstreams between turns

## Already Executed

- `TASK-106`: Python CI baseline
- `TASK-114`: governed multi-stack static analysis for the active non-Python surface
- `TASK-116`: Python type checking
- `TASK-117`: explicit TOML and structured JSON validation
- `TASK-118`: governed SQL static analysis
- `TASK-119`: software-composition analysis for Python and Node
- `TASK-120`: `pre-commit` orchestration
- `TASK-121`: repository checkpoint and remote-sync governance
- `TASK-122`: local Git sync audit automation and scheduled Windows reminder path
- current governed stack is implemented and validated for:
  - Python: `ruff`, `pytest`, `pyright`, `compileall`
  - Apps Script: `eslint`
  - Markdown: `markdownlint-cli2`
  - YAML: `yamllint`
  - GitHub Actions: `actionlint`
  - Shell: `shellcheck`
  - PowerShell: `PSScriptAnalyzer`
  - SQL: `sqlfluff`
  - dependency audit: `pip-audit`, `npm audit`
  - local orchestration: `pre-commit`
  - repository hygiene: `git_sync_audit.py` plus opt-in scheduled Windows audit

## Explicitly Deferred

- `TASK-115`: security hardening of the dev bridge and broader repo posture

This is intentionally deferred until after the functional MVP and planned backlog are substantially complete, unless the risk posture changes materially.

## Usage Rule

When a proposal is approved in conversation:

1. add or update a concrete backlog task
2. reflect status here as `executed`, `approved but not yet executed`, or `deferred`
3. only then refer to it as part of the active execution plan
