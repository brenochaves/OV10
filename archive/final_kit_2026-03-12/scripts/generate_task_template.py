#!/usr/bin/env python3
from pathlib import Path

target = Path('.codex/BACKLOG.md')

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

if __name__ == '__main__':
    if not target.exists():
        raise SystemExit('missing .codex/BACKLOG.md')
    with target.open('a', encoding='utf-8') as f:
        f.write(TEMPLATE)
    print('task template appended')
