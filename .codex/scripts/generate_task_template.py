#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path(".codex/BACKLOG.md")

TEMPLATE = """
## TASK-NEW
status: TODO
priority: P2
type: fill_me
summary: describe a real repository-grounded task
acceptance:
- define observable completion criteria

dependencies: none
notes: include evidence source
"""


def main() -> int:
    if not TARGET.exists():
        raise SystemExit("missing .codex/BACKLOG.md")
    with TARGET.open("a", encoding="utf-8") as handle:
        handle.write(TEMPLATE)
    print("task template appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
