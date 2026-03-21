# Codex Autonomous Engineering Kit v6 Final

Merged repository-centric kit for disciplined autonomous development with long-running stability, project-memory preservation, specialist agent roles, and remote supervision.

## Design intent

This kit is meant to be copied into the root of an existing repository and then adapted by Codex without overwriting mature project decisions.

## What this version adds

- canonical `.codex/` single source of truth
- project memory and repository knowledge mapping
- explicit execution loop with local-block vs hard-stop handling
- specialist team roles beyond planner/coder/tester/reviewer
- context rotation for long-running sessions
- dynamic task prioritization support
- watchdog / monitor scripts
- prompts for integration, memory build, autonomous start, specialist-team activation, and resume flows
- practical VS Code Tunnel setup for web/smartphone supervision

## Recommended adoption order

1. Copy the kit into the repository root.
2. Ask Codex to run `.codex/prompts/01_ANALYZE_INTEGRATION.txt`.
3. Review `.codex/INTEGRATION_REPORT.md`.
4. Ask Codex to run `.codex/prompts/02_BUILD_PROJECT_MEMORY.txt`.
5. Review and refine `.codex/PROJECT_MEMORY_INDEX.md`, `.codex/ARCHITECTURE_MAP.md`, and `.codex/REPOSITORY_KNOWLEDGE_GRAPH.md`.
6. Seed `.codex/BACKLOG.md` with real project tasks.
7. Ask Codex to run `.codex/prompts/03_START_AUTONOMOUS_MODE.txt`.
8. If desired, activate specialist roles with `.codex/prompts/06_ENABLE_SPECIALIST_TEAM.txt`.

## Canonical files

All operational truth lives under `.codex/`.

Compatibility folders under `docs/`, `agents/`, and `tasks/` exist only to reduce friction during migration.
