#!/usr/bin/env python3
from pathlib import Path
import re

backlog = Path('.codex/BACKLOG.md')

PRIORITY_HINTS = [
    (re.compile(r'\b(security|credential|secret|auth|permission)\b', re.I), 'P0'),
    (re.compile(r'\b(bug|fail|regression|incident|crash)\b', re.I), 'P1'),
    (re.compile(r'\b(test|coverage|validation)\b', re.I), 'P1'),
    (re.compile(r'\b(performance|latency|memory|cpu)\b', re.I), 'P2'),
    (re.compile(r'\b(doc|documentation|readme|operator)\b', re.I), 'P3'),
]

if __name__ == '__main__':
    if not backlog.exists():
        raise SystemExit('missing .codex/BACKLOG.md')
    text = backlog.read_text(encoding='utf-8')
    for pattern, priority in PRIORITY_HINTS:
        if pattern.search(text):
            pass
    print('review backlog and adjust priorities conservatively; this script is a heuristic stub by design')
