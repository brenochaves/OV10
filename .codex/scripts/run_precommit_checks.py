from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WINDOWS_PROJECT_PYTHON = REPO_ROOT / ".venv312" / "Scripts" / "python.exe"
POSIX_PROJECT_PYTHON = REPO_ROOT / ".venv312" / "bin" / "python"


def main() -> int:
    project_python = _resolve_project_python()
    actionlint_path = _resolve_binary("actionlint")
    shellcheck_path = _resolve_binary("shellcheck")
    npm_path = _resolve_binary("npm")
    npx_path = _resolve_binary("npx")

    commands = [
        (
            "Ruff check",
            [str(project_python), "-m", "ruff", "check", "."],
        ),
        (
            "Ruff format check",
            [str(project_python), "-m", "ruff", "format", ".", "--check"],
        ),
        (
            "Pyright",
            [npx_path, "pyright"],
        ),
        (
            "ESLint Apps Script",
            [npm_path, "run", "lint:apps-script"],
        ),
        (
            "Markdownlint",
            [npm_path, "run", "lint:markdown"],
        ),
        (
            "YamlLint",
            [
                str(project_python),
                "-m",
                "yamllint",
                ".github/workflows/ci.yml",
                ".codex/SYSTEM_STATE.yaml",
            ],
        ),
        (
            "Actionlint",
            [actionlint_path],
        ),
        (
            "ShellCheck",
            [shellcheck_path, ".codex/scripts/watchdog_loop.sh"],
        ),
        (
            "PSScriptAnalyzer",
            [
                "pwsh",
                "-NoLogo",
                "-NoProfile",
                "-Command",
                (
                    "Invoke-ScriptAnalyzer -Path '.codex/scripts/*.ps1' "
                    "-Settings 'PSScriptAnalyzerSettings.psd1' -EnableExit"
                ),
            ],
        ),
        (
            "SQLFluff",
            [str(project_python), "-m", "sqlfluff", "lint", "sql"],
        ),
    ]

    for label, command in commands:
        print(f"[pre-commit] {label}: {' '.join(command)}")
        subprocess.run(command, cwd=REPO_ROOT, check=True)

    return 0


def _resolve_project_python() -> Path:
    if WINDOWS_PROJECT_PYTHON.exists():
        return WINDOWS_PROJECT_PYTHON
    if POSIX_PROJECT_PYTHON.exists():
        return POSIX_PROJECT_PYTHON
    raise FileNotFoundError("Could not locate the governed .venv312 Python interpreter.")


def _resolve_binary(binary_name: str) -> str:
    resolved = shutil.which(binary_name)
    if resolved is not None:
        return resolved
    resolved = shutil.which(f"{binary_name}.cmd")
    if resolved is not None:
        return resolved
    resolved = shutil.which(f"{binary_name}.exe")
    if resolved is not None:
        return resolved

    nodejs_program_files = Path("C:/Program Files/nodejs")
    for candidate_name in (binary_name, f"{binary_name}.cmd", f"{binary_name}.exe"):
        candidate = nodejs_program_files / candidate_name
        if candidate.exists():
            return str(candidate)

    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    suffix = ".exe" if not binary_name.endswith(".exe") else ""
    pattern = binary_name if suffix == "" else f"{binary_name}{suffix}"
    for candidate in winget_packages.rglob(pattern):
        return str(candidate)

    raise FileNotFoundError(f"Required binary not found: {binary_name}")


if __name__ == "__main__":
    raise SystemExit(main())
