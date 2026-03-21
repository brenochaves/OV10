# ADR 0007: Adopt Final Kit Selectively As An OV10 Control Plane

Date: 2026-03-12

## Status

Accepted

Note: the original `final_kit/` directory was archived on 2026-03-21 under `archive/final_kit_2026-03-12/` after the active control-plane content had been absorbed into the root `.codex/`.

## Context

The repository gained a `final_kit/` directory containing generic autonomy scaffolding for Codex: `.codex` state files, prompts, specialist-role files, and helper scripts such as a watchdog loop and a repo monitor.

OV10 already had stronger project-specific assets than the kit:

- governed implementation under `src/ov10/`
- automated tests under `tests/`
- accepted ADRs under `docs/adr/`
- reverse engineering evidence under `docs/diagnostics/`
- an operator runbook under `docs/operations/SETUP_AND_USAGE.md`

Copying the kit wholesale would lower signal because some files were placeholders, one script was syntactically broken, and the kit had no awareness of OV10-specific source-of-truth priorities.

## Decision

Adopt `final_kit` selectively under a new root `.codex/` control plane with OV10-specific content.

Rules of adoption:

- OV10 code, tests, ADRs, diagnostics, and operator docs remain higher-trust than `.codex/`
- kit placeholders are rewritten using repository evidence
- broken kit scripts are repaired before adoption
- `watchdog_loop.sh` is ported to Windows with equivalent `.ps1` and `.bat` variants
- `repo_monitor.py` is allowed as an explicit operator-controlled automation even though it can trigger repeated `codex continue` runs on frequent `HEAD` changes

## Consequences

- OV10 now has a durable autonomy control plane without replacing stronger repository artifacts
- backlog, task graph, context, memory, prompts, and specialist roles are available in repo-local form
- long-running automation is available on Windows, but remains opt-in and should be used with operator discipline
- the integration remains traceable through this ADR, `.codex/INTEGRATION_REPORT.md`, and the updated runbook
