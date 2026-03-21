#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

DEFAULT_MAX_HOURS_SINCE_COMMIT_WARNING: Final[float] = 12.0
DEFAULT_MAX_HOURS_SINCE_COMMIT_ERROR: Final[float] = 24.0
DEFAULT_MAX_UNTRACKED_FILES_WARNING: Final[int] = 20
DEFAULT_MAX_UNTRACKED_FILES_ERROR: Final[int] = 100
DEFAULT_MAX_CHANGED_FILES_WARNING: Final[int] = 25
DEFAULT_MAX_CHANGED_FILES_ERROR: Final[int] = 75
DEFAULT_MAX_AHEAD_COMMITS_WARNING: Final[int] = 3
DEFAULT_MAX_AHEAD_COMMITS_ERROR: Final[int] = 10
DEFAULT_MAX_BEHIND_COMMITS_WARNING: Final[int] = 1


@dataclass(frozen=True)
class AuditThresholds:
    max_hours_since_commit_warning: float = DEFAULT_MAX_HOURS_SINCE_COMMIT_WARNING
    max_hours_since_commit_error: float = DEFAULT_MAX_HOURS_SINCE_COMMIT_ERROR
    max_untracked_files_warning: int = DEFAULT_MAX_UNTRACKED_FILES_WARNING
    max_untracked_files_error: int = DEFAULT_MAX_UNTRACKED_FILES_ERROR
    max_changed_files_warning: int = DEFAULT_MAX_CHANGED_FILES_WARNING
    max_changed_files_error: int = DEFAULT_MAX_CHANGED_FILES_ERROR
    max_ahead_commits_warning: int = DEFAULT_MAX_AHEAD_COMMITS_WARNING
    max_ahead_commits_error: int = DEFAULT_MAX_AHEAD_COMMITS_ERROR
    max_behind_commits_warning: int = DEFAULT_MAX_BEHIND_COMMITS_WARNING


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class GitSyncAuditReport:
    generated_at: str
    repository_root: str
    branch: str | None
    upstream: str | None
    head: str | None
    tracked_file_count: int
    top_level_untracked_entries: int
    untracked_file_count: int
    changed_tracked_file_count: int
    ahead_commits: int
    behind_commits: int
    last_commit_iso: str | None
    hours_since_last_commit: float | None
    thresholds: dict[str, float | int]
    findings: list[dict[str, str]]
    status: str
    remediation: list[str]


def _run_git(args: list[str], repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_output(args: list[str], repo_root: Path) -> str:
    result = _run_git(args, repo_root)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def _status_lines(repo_root: Path, *, all_untracked: bool) -> list[str]:
    args = ["status", "--porcelain"]
    if all_untracked:
        args.append("--untracked-files=all")
    output = _git_output(args, repo_root)
    if not output:
        return []
    return [line for line in output.splitlines() if line.strip()]


def _branch_metrics(repo_root: Path) -> tuple[str | None, str | None, int, int, str | None]:
    output = _git_output(["status", "--porcelain=v2", "--branch"], repo_root)
    branch: str | None = None
    upstream: str | None = None
    ahead = 0
    behind = 0
    head: str | None = None
    for line in output.splitlines():
        if line.startswith("# branch.head "):
            branch = line.removeprefix("# branch.head ").strip()
        elif line.startswith("# branch.upstream "):
            upstream = line.removeprefix("# branch.upstream ").strip()
        elif line.startswith("# branch.ab "):
            fragment = line.removeprefix("# branch.ab ").strip()
            for part in fragment.split():
                if part.startswith("+"):
                    ahead = int(part[1:])
                elif part.startswith("-"):
                    behind = int(part[1:])
        elif line.startswith("# branch.oid "):
            head = line.removeprefix("# branch.oid ").strip()
    return branch, upstream, ahead, behind, head


def _last_commit_metrics(repo_root: Path) -> tuple[str | None, float | None]:
    timestamp_text = _git_output(["log", "-1", "--format=%ct"], repo_root)
    if not timestamp_text:
        return None, None
    timestamp = int(timestamp_text)
    commit_time = datetime.fromtimestamp(timestamp, tz=UTC)
    now = datetime.now(tz=UTC)
    delta_hours = round((now - commit_time).total_seconds() / 3600, 2)
    return commit_time.isoformat(), delta_hours


def _tracked_file_count(repo_root: Path) -> int:
    output = _git_output(["ls-files"], repo_root)
    if not output:
        return 0
    return len(output.splitlines())


def _classify_status(
    findings: list[AuditFinding],
    *,
    fail_on: str,
) -> int:
    if any(finding.severity == "error" for finding in findings):
        return 2 if fail_on in {"error", "warning"} else 0
    if any(finding.severity == "warning" for finding in findings):
        return 1 if fail_on == "warning" else 0
    return 0


def _overall_status(findings: list[AuditFinding]) -> str:
    if any(finding.severity == "error" for finding in findings):
        return "error"
    if any(finding.severity == "warning" for finding in findings):
        return "warning"
    return "ok"


def _build_findings(
    *,
    tracked_file_count: int,
    top_level_untracked_entries: int,
    untracked_file_count: int,
    changed_tracked_file_count: int,
    ahead_commits: int,
    behind_commits: int,
    upstream: str | None,
    hours_since_last_commit: float | None,
    thresholds: AuditThresholds,
) -> list[AuditFinding]:
    findings: list[AuditFinding] = []

    if upstream is None:
        findings.append(
            AuditFinding(
                severity="error",
                code="missing_upstream",
                message=(
                    "Current branch has no upstream; commit and push governance cannot be enforced."
                ),
            )
        )

    if tracked_file_count == 0:
        findings.append(
            AuditFinding(
                severity="error",
                code="no_tracked_files",
                message="Repository has no tracked files.",
            )
        )
    elif untracked_file_count > tracked_file_count * 5:
        findings.append(
            AuditFinding(
                severity="error",
                code="versioning_gap",
                message=(
                    "Untracked file count exceeds five times the tracked file count; "
                    "the repository is materially under-versioned."
                ),
            )
        )

    if untracked_file_count >= thresholds.max_untracked_files_error:
        findings.append(
            AuditFinding(
                severity="error",
                code="excessive_untracked_files",
                message=(
                    f"{untracked_file_count} untracked files exceed the error threshold "
                    f"of {thresholds.max_untracked_files_error}."
                ),
            )
        )
    elif untracked_file_count >= thresholds.max_untracked_files_warning:
        findings.append(
            AuditFinding(
                severity="warning",
                code="untracked_files_present",
                message=(
                    f"{untracked_file_count} untracked files exceed the warning threshold "
                    f"of {thresholds.max_untracked_files_warning}."
                ),
            )
        )

    if changed_tracked_file_count >= thresholds.max_changed_files_error:
        findings.append(
            AuditFinding(
                severity="error",
                code="excessive_changed_files",
                message=(
                    f"{changed_tracked_file_count} tracked changed files exceed the "
                    "error threshold "
                    f"of {thresholds.max_changed_files_error}."
                ),
            )
        )
    elif changed_tracked_file_count >= thresholds.max_changed_files_warning:
        findings.append(
            AuditFinding(
                severity="warning",
                code="many_changed_files",
                message=(
                    f"{changed_tracked_file_count} tracked changed files exceed the "
                    "warning threshold "
                    f"of {thresholds.max_changed_files_warning}."
                ),
            )
        )

    if hours_since_last_commit is not None and (
        untracked_file_count > 0 or changed_tracked_file_count > 0
    ):
        if hours_since_last_commit >= thresholds.max_hours_since_commit_error:
            findings.append(
                AuditFinding(
                    severity="error",
                    code="stale_dirty_worktree",
                    message=(
                        "Dirty worktree has been open for "
                        f"{hours_since_last_commit:.2f} hours since the last commit, "
                        "exceeding the error threshold of "
                        f"{thresholds.max_hours_since_commit_error} hours."
                    ),
                )
            )
        elif hours_since_last_commit >= thresholds.max_hours_since_commit_warning:
            findings.append(
                AuditFinding(
                    severity="warning",
                    code="aging_dirty_worktree",
                    message=(
                        "Dirty worktree has been open for "
                        f"{hours_since_last_commit:.2f} hours since the last commit, "
                        "exceeding the warning threshold of "
                        f"{thresholds.max_hours_since_commit_warning} hours."
                    ),
                )
            )

    if ahead_commits >= thresholds.max_ahead_commits_error:
        findings.append(
            AuditFinding(
                severity="error",
                code="too_many_unpushed_commits",
                message=(
                    f"Branch is {ahead_commits} commits ahead of upstream, "
                    "exceeding the error threshold "
                    f"of {thresholds.max_ahead_commits_error}."
                ),
            )
        )
    elif ahead_commits >= thresholds.max_ahead_commits_warning:
        findings.append(
            AuditFinding(
                severity="warning",
                code="unpushed_commits_present",
                message=(
                    f"Branch is {ahead_commits} commits ahead of upstream, "
                    "exceeding the warning threshold "
                    f"of {thresholds.max_ahead_commits_warning}."
                ),
            )
        )

    if behind_commits >= thresholds.max_behind_commits_warning:
        findings.append(
            AuditFinding(
                severity="warning",
                code="upstream_ahead",
                message=(
                    f"Upstream is {behind_commits} commits ahead of the local branch; "
                    "pull or rebase before starting a long new workstream."
                ),
            )
        )

    if top_level_untracked_entries > 0:
        findings.append(
            AuditFinding(
                severity="warning",
                code="top_level_untracked_entries",
                message=(
                    f"{top_level_untracked_entries} top-level untracked entries are present. "
                    "Classify them as tracked or ignored before ending the work session."
                ),
            )
        )

    return findings


def _build_remediation(
    *,
    branch: str | None,
    findings: list[AuditFinding],
) -> list[str]:
    remediation = [
        "Inspect the exact worktree with `git status --short --untracked-files=all`.",
        "Move generated or local-only artifacts under an ignored path before ending the session.",
        "Create a local checkpoint commit after the current validated slice is coherent.",
    ]
    if any(
        finding.code in {"unpushed_commits_present", "too_many_unpushed_commits"}
        for finding in findings
    ):
        branch_name = branch or "main"
        remediation.append(f"Push the checkpoint branch with `git push origin {branch_name}`.")
    if any(finding.code == "upstream_ahead" for finding in findings):
        remediation.append(
            "Reconcile upstream changes before starting another long autonomous cycle."
        )
    return remediation


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: GitSyncAuditReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _append_jsonl(path: Path, payload: GitSyncAuditReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(payload), ensure_ascii=False) + "\n")


def _to_markdown(payload: GitSyncAuditReport) -> str:
    lines = [
        "# Git Sync Audit",
        "",
        f"- generated_at: `{payload.generated_at}`",
        f"- repository_root: `{payload.repository_root}`",
        f"- branch: `{payload.branch}`",
        f"- upstream: `{payload.upstream}`",
        f"- head: `{payload.head}`",
        f"- tracked_file_count: `{payload.tracked_file_count}`",
        f"- top_level_untracked_entries: `{payload.top_level_untracked_entries}`",
        f"- untracked_file_count: `{payload.untracked_file_count}`",
        f"- changed_tracked_file_count: `{payload.changed_tracked_file_count}`",
        f"- ahead_commits: `{payload.ahead_commits}`",
        f"- behind_commits: `{payload.behind_commits}`",
        f"- last_commit_iso: `{payload.last_commit_iso}`",
        f"- hours_since_last_commit: `{payload.hours_since_last_commit}`",
        f"- status: `{payload.status}`",
        "",
        "## Findings",
        "",
    ]
    if payload.findings:
        for finding in payload.findings:
            lines.append(f"- `{finding['severity']}` `{finding['code']}`: {finding['message']}")
    else:
        lines.append("- `ok`: repository sync posture is within the configured thresholds.")
    lines.extend(["", "## Remediation", ""])
    for step in payload.remediation:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local Git checkpoint and push posture.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root to inspect.",
    )
    parser.add_argument(
        "--write-json",
        type=Path,
        default=None,
        help="Optional path for a structured JSON report.",
    )
    parser.add_argument(
        "--write-markdown",
        type=Path,
        default=None,
        help="Optional path for a Markdown summary report.",
    )
    parser.add_argument(
        "--append-jsonl",
        type=Path,
        default=None,
        help="Optional path for append-only JSONL audit history.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["none", "warning", "error"],
        default="error",
        help="Exit policy for findings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    thresholds = AuditThresholds()

    try:
        _git_output(["rev-parse", "--is-inside-work-tree"], repo_root)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    top_level_status = _status_lines(repo_root, all_untracked=False)
    full_status = _status_lines(repo_root, all_untracked=True)
    branch, upstream, ahead_commits, behind_commits, head = _branch_metrics(repo_root)
    last_commit_iso, hours_since_last_commit = _last_commit_metrics(repo_root)
    tracked_file_count = _tracked_file_count(repo_root)
    top_level_untracked_entries = sum(1 for line in top_level_status if line.startswith("?? "))
    untracked_file_count = sum(1 for line in full_status if line.startswith("?? "))
    changed_tracked_file_count = sum(1 for line in full_status if not line.startswith("?? "))

    findings = _build_findings(
        tracked_file_count=tracked_file_count,
        top_level_untracked_entries=top_level_untracked_entries,
        untracked_file_count=untracked_file_count,
        changed_tracked_file_count=changed_tracked_file_count,
        ahead_commits=ahead_commits,
        behind_commits=behind_commits,
        upstream=upstream,
        hours_since_last_commit=hours_since_last_commit,
        thresholds=thresholds,
    )

    report = GitSyncAuditReport(
        generated_at=datetime.now(tz=UTC).isoformat(),
        repository_root=str(repo_root),
        branch=branch,
        upstream=upstream,
        head=head,
        tracked_file_count=tracked_file_count,
        top_level_untracked_entries=top_level_untracked_entries,
        untracked_file_count=untracked_file_count,
        changed_tracked_file_count=changed_tracked_file_count,
        ahead_commits=ahead_commits,
        behind_commits=behind_commits,
        last_commit_iso=last_commit_iso,
        hours_since_last_commit=hours_since_last_commit,
        thresholds=asdict(thresholds),
        findings=[asdict(finding) for finding in findings],
        status=_overall_status(findings),
        remediation=_build_remediation(branch=branch, findings=findings),
    )

    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))

    if args.write_json is not None:
        _write_json(args.write_json.resolve(), report)
    if args.write_markdown is not None:
        _write_text(args.write_markdown.resolve(), _to_markdown(report))
    if args.append_jsonl is not None:
        _append_jsonl(args.append_jsonl.resolve(), report)

    return _classify_status(findings, fail_on=args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
