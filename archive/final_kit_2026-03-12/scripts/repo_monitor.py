#!/usr/bin/env python3
import subprocess
import time

POLL_SECONDS = 120
last = None

def git_head():
    try:
        result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=False)
        return result.stdout.strip() or None
    except Exception:
        return None

if __name__ == '__main__':
    last = git_head()
    while True:
        current = git_head()
        if current and current != last:
            subprocess.run(['codex', 'continue'], check=False)
            last = current
        time.sleep(POLL_SECONDS)
