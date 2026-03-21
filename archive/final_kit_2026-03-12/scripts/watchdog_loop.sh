#!/usr/bin/env bash
set -u

INTERVAL_SECONDS="${INTERVAL_SECONDS:-300}"

while true; do
  codex continue || true
  sleep "$INTERVAL_SECONDS"
done
