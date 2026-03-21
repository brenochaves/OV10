# VS Code Environment Handover

Date: 2026-03-21

## What was changed

- normalized global VS Code settings to keep OpenAI/Codex available while keeping GitHub Copilot disabled
- disabled ChatGPT auto-open on startup
- fixed PowerShell `code` resolution by prepending the VS Code CLI `bin` path in the PowerShell profile
- installed the core extension baseline:
  - `ms-python.python`
  - `ms-python.vscode-pylance`
  - `ms-python.debugpy`
  - `charliermarsh.ruff`
  - `ms-vscode.powershell`
  - `esbenp.prettier-vscode`
  - `redhat.vscode-yaml`
  - `tamasfe.even-better-toml`
  - `editorconfig.editorconfig`
  - `usernamehw.errorlens`
  - `eamodio.gitlens`
  - `streetsidesoftware.code-spell-checker`
  - `yzhang.markdown-all-in-one`
  - `davidanson.vscode-markdownlint`
  - `bierner.markdown-mermaid`

## OV10 repo changes

- added `.editorconfig`
- added `.vscode/settings.json`
- added `.vscode/extensions.json`
- added `.vscode/tasks.json`
- added `.vscode/launch.json`
- added `.vscode/snippets.code-snippets`
- updated `.gitignore` to allow those workspace files to be tracked

## Intended OV10 workspace behavior

- default interpreter: `.venv312\Scripts\python.exe`
- pytest wired for `tests/`
- debug configs exist for:
  - `ov10.cli`
  - `pytest`
  - legacy `main.py`
- tasks exist for:
  - pytest
  - ruff check
  - ruff format
  - CLI help

## Validation already performed

- `code --list-extensions --show-versions` works from PowerShell
- `C:\git\OV10\.venv312\Scripts\python.exe -m pytest -q` passed with `29 passed`

## Outstanding issue for the OV10 project agent

`ruff check .` is still failing, but the failures surfaced during environment validation are in mixed-scope files:

- root legacy scripts:
  - `main.py`
  - `leitor_planilha.py`
  - `consolidar_posicao.py`
  - `exportador.py`
- `final_kit/scripts/*`

This means the next agent should make an explicit scope decision before "fixing lint":

1. keep repo-wide lint as the standard and clean those files
2. or narrow lint scope to the governed OV10 surface first (`src/ov10`, `tests`, selected tooling)

Do not treat the lint failure as a VS Code setup failure. The environment is working; the repo is not fully lint-clean.
