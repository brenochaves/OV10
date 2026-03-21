#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

summary = Path('.codex/memory/context_summary.md')
snapshot = Path('.codex/memory/context_snapshot.md')
context = Path('.codex/CONTEXT.md')

if __name__ == '__main__':
    ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    summary_text = summary.read_text(encoding='utf-8') if summary.exists() else '# CONTEXT SUMMARY

'
    context_text = context.read_text(encoding='utf-8') if context.exists() else '# CONTEXT

'
    snapshot.write_text(
        f'# CONTEXT SNAPSHOT

Generated: {ts}

## Summary

{summary_text}

## Full context excerpt

{context_text[:8000]}
',
        encoding='utf-8'
    )
    print('context snapshot refreshed')
