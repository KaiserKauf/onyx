---
name: aleiva-autopilot
description: Runs the Aleiva autonomous build loop on Onyx (orchestrator, guardrails, second brain, dashboard). Use when extending Aleiva, continuing feat-aleiva-mvp work, or when the user asks to build weiter without approval pauses.
disable-model-invocation: true
---

# Aleiva Autopilot

Autonomous workflow for AleivaOS-style development on this Onyx fork.

## When to use

- User says: build weiter, orchestrate, autonomous Aleiva, feat-aleiva-mvp
- Extending `backend/onyx/aleiva_core/`, Aleiva API, or `/aleiva` dashboard
- After spec/plan approval in `docs/superpowers/specs/2026-05-23-aleiva-hybrid-mvp-design.md`

## Worktree and branch

```text
Branch: feat-aleiva-mvp
Worktree: .worktrees/a   (gitignored; create with git worktree add .worktrees/a feat-aleiva-mvp)
Setup:   uv sync         (once per worktree)
```

Prefer `uv run` for pytest/ruff. Avoid npm install, docker, and git push unless the user explicitly asks.

## Subagent gates (required after each task cluster)

1. **aleiva-spec-guardian** — spec compliance, scope, non-forgetting artifacts
2. **aleiva-quality-reviewer** — correctness, edge cases, tests

Delegate implementation with **aleiva-orchestrator**. Use specialists when needed:

| Task | Subagent |
|------|----------|
| Dashboard UI | aleiva-frontend-builder |
| Second-brain hygiene | aleiva-memory-curator |
| Playwright E2E | aleiva-e2e-validator |
| Commit / push / PR | aleiva-ship-agent |

## Build loop

```text
plan -> execute -> verify -> learn
```

Copy and track:

```text
- [ ] Read spec section / plan task
- [ ] Implement minimal scoped change
- [ ] Run unit tests (below)
- [ ] Run ruff on touched paths
- [ ] spec-guardian pass
- [ ] quality-reviewer pass
- [ ] Persist learnings (second brain + completeness gate)
```

## Verification commands

```bash
uv run python -m pytest backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva -q
uv run ruff check backend/onyx/aleiva_core backend/onyx/server/features/aleiva backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva
```

Frontend (when `web/node_modules` exists):

```bash
cd web && npx playwright test tests/e2e/aleiva/aleiva_dashboard.spec.ts --project admin
```

## Non-forgetting protocol

Before marking a run complete, ensure:

- goal + success criteria
- decisions / rationale
- change summary
- verification outcomes
- at least one learning entry

Use `validate_run_completeness` in `backend/onyx/aleiva_core/events.py`.

## Design continuity

- Matrix UI at `/aleiva`: high-contrast, interactive, guided onboarding
- API via BFF only: `/api/aleiva/*` (never `localhost:8080` directly)
- Voice/trading panels must not bypass guardrails

## Commit policy

- Do **not** commit until user asks or **aleiva-ship-agent** is invoked
- Ship only Aleiva-scoped paths; exclude unrelated diffs

## Additional resources

- API paths, modules, CLI notes: [reference.md](reference.md)
- Product spec: `docs/superpowers/specs/2026-05-23-aleiva-hybrid-mvp-design.md`
- Onyx CLI dry-run: `.cursor/skills/onyx-cli/SKILL.md`
