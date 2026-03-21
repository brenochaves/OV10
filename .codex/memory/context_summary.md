# CONTEXT SUMMARY

- OV10 already has a stronger domain core than `final_kit`; `.codex/` is an auxiliary control plane.
- Trusted implementation path: `src/ov10/`; trusted validation path: `tests/`; trusted decisions: `docs/adr/`.
- Trusted environment: `.venv312`; do not treat the global Python 3.13 install as the primary path.
- Synthetic workbook generation now exists under `src/ov10/testing/` for controlled local scenarios.
- Workbook-based config loading now exists; the next high-value task is reducing `system_cash_account_used`.
- Monitor and watchdog scripts are operator-controlled automation, not mandatory background services.
