#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime

POLL_SECONDS = int(os.environ.get("POLL_SECONDS", "120"))
CONTINUE_COMMAND = os.environ.get("CODEX_CONTINUE_COMMAND", "codex continue")


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def git_head() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    head = result.stdout.strip()
    return head or None


def run_continue() -> None:
    print(f"[{_timestamp()}] HEAD changed; running `{CONTINUE_COMMAND}`")
    subprocess.run(CONTINUE_COMMAND, shell=True, check=False)


def main() -> int:
    last = git_head()
    print(f"[{_timestamp()}] repo monitor started; poll_seconds={POLL_SECONDS}; last_head={last}")
    while True:
        current = git_head()
        if current and current != last:
            run_continue()
            last = current
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
