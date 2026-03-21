# QUALITY GATES

Quality gates must match the actual OV10 repository stack.

## Default gates

1. do not knowingly break the `.venv312` execution path
2. prefer the smallest trustworthy validation set for each change
3. document validation gaps honestly
4. do not claim full coverage unless evidence exists
5. do not merge architectural changes silently
6. update operator-facing docs if behavior changes materially

## Validation guidance

Prefer this order:
- targeted tests near changed behavior
- `.\.venv312\Scripts\python.exe -m pytest -q`
- `.\.venv312\Scripts\python.exe -m ruff check .`
- `.\.venv312\Scripts\python.exe -m ruff format . --check`
- `npm run typecheck:python`
- `npm run lint:apps-script`
- `npm run lint:markdown`
- `.\.venv312\Scripts\python.exe -m yamllint .github\workflows\ci.yml .codex\SYSTEM_STATE.yaml`
- `actionlint`
- `shellcheck .codex/scripts/watchdog_loop.sh`
- `pwsh -NoLogo -NoProfile -Command "Invoke-ScriptAnalyzer -Path '.codex/scripts/*.ps1' -Settings 'PSScriptAnalyzerSettings.psd1' -EnableExit"`
- `.\.venv312\Scripts\python.exe -m sqlfluff lint sql`
- `.\.venv312\Scripts\python.exe -m compileall .codex\scripts`
- smoke validation for affected CLI entry points
- `.\.venv312\Scripts\python.exe -m pip_audit --progress-spinner off --skip-editable` for dependency-sensitive changes or full release validation
- `npm run audit:node` for dependency-sensitive changes or full release validation
- `.\.venv312\Scripts\python.exe .codex\scripts\git_sync_audit.py --fail-on warning` before ending a long work session or enabling unattended continuation

## Current environment note

The global Python 3.13 installation is not the trusted project path.
Use `.venv312` for project validation unless a newer verified environment supersedes it.

## Ruff policy note

`ruff check .` is governed through `pyproject.toml`.

It intentionally covers the supported OV10 surface while excluding:

- legacy exploratory root-level scripts
- archived scaffolding material under `archive/`

## Multi-stack policy note

Current governed extended gates are:

- ESLint for `apps_script_debug_bridge/**/*.gs`
- Markdownlint for active repo docs and `.codex/`
- Pyright for `src/ov10`
- YamlLint for GitHub Actions and `.codex/SYSTEM_STATE.yaml`
- Actionlint for workflow semantics
- ShellCheck for `.codex/scripts/watchdog_loop.sh`
- PSScriptAnalyzer for `.codex/scripts/*.ps1`
- SQLFluff for governed SQL under `sql/`
- `pip-audit` for Python dependency scanning
- `npm audit` for Node dependency scanning

## Pre-commit policy note

`.pre-commit-config.yaml` is a local orchestrator only.

It exists to run the same governed checks before commit through
`.codex/scripts/run_precommit_checks.py`; it is not a second source of truth.

## Repository sync policy note

Quality validation does not by itself protect against repository-loss risk.

Use `docs/operations/GIT_CHECKPOINT_POLICY.md` and `.codex/scripts/git_sync_audit.py`
to keep checkpoint cadence and remote-sync posture visible.
