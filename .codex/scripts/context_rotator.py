#!/usr/bin/env python3
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

SUMMARY_PATH = Path(".codex/memory/context_summary.md")
SNAPSHOT_PATH = Path(".codex/memory/context_snapshot.md")
CONTEXT_PATH = Path(".codex/CONTEXT.md")
MAX_CONTEXT_CHARS = 8000


def _read_text(path: Path, default: str) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return default


def main() -> int:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    summary_text = _read_text(SUMMARY_PATH, "# CONTEXT SUMMARY\n\n")
    context_text = _read_text(CONTEXT_PATH, "# CONTEXT\n\n")

    SNAPSHOT_PATH.write_text(
        "\n".join(
            [
                "# CONTEXT SNAPSHOT",
                "",
                f"Generated: {timestamp}",
                "",
                "## Summary",
                "",
                summary_text.rstrip(),
                "",
                "## Full context excerpt",
                "",
                context_text[:MAX_CONTEXT_CHARS].rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    print("context snapshot refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
