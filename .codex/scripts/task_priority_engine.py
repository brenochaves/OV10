#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

BACKLOG_PATH = Path(".codex/BACKLOG.md")

PRIORITY_HINTS = [
    (re.compile(r"\b(security|credential|secret|auth|permission)\b", re.I), "P0"),
    (re.compile(r"\b(bug|fail|regression|incident|crash)\b", re.I), "P1"),
    (re.compile(r"\b(test|coverage|validation|reconciliation)\b", re.I), "P1"),
    (re.compile(r"\b(performance|latency|memory|cpu)\b", re.I), "P2"),
    (re.compile(r"\b(doc|documentation|readme|operator)\b", re.I), "P3"),
]


def main() -> int:
    if not BACKLOG_PATH.exists():
        raise SystemExit("missing .codex/BACKLOG.md")

    backlog_text = BACKLOG_PATH.read_text(encoding="utf-8")
    suggestions: list[str] = []
    for pattern, priority in PRIORITY_HINTS:
        if pattern.search(backlog_text):
            suggestions.append(priority)

    print("review backlog and adjust priorities conservatively; this script is heuristic only")
    if suggestions:
        for priority in suggestions:
            print(f"- observed hint suggesting at least one {priority} item")
    else:
        print("- no heuristic hints detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
