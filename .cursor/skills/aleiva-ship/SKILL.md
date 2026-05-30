---
name: aleiva-ship
description: Ships Aleiva changes on feat-aleiva-mvp: scoped staging, preflight tests, commit, push, and PR draft. Use when the user asks to commit, push, ship, or open a PR for Aleiva work.
disable-model-invocation: true
---

# Aleiva Ship

Release workflow for Aleiva on branch `feat-aleiva-mvp`.

## Preflight

```bash
cd .worktrees/a   # if using isolated worktree
git branch --show-current   # must be feat-aleiva-mvp
uv run python -m pytest backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva -q
uv run ruff check backend/onyx/aleiva_core backend/onyx/server/features/aleiva backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva
```

Do not commit if tests fail.

## Stage scope

Include only Aleiva-related paths:

- `backend/onyx/aleiva_core/**`
- `backend/onyx/server/features/aleiva/**`
- `backend/tests/unit/onyx/aleiva_core/**`
- `backend/tests/unit/server/features/aleiva/**`
- `web/src/app/aleiva/**`
- `web/tests/e2e/aleiva/**`
- `web/src/lib/admin-routes.ts`, `swr-keys.ts`, `AdminSidebar.tsx` (when Aleiva-touched)
- `docs/superpowers/specs/*aleiva*`
- `.cursor/agents/aleiva-*.md`, `.cursor/skills/aleiva-*/` (when shipping tooling)
- `AGENTS.md` (Aleiva learnings section only)
- `cli/internal/embedded/SKILL.md` (Aleiva CLI notes only)

Exclude: `.worktrees/`, `.venv/`, unrelated backend/web churn.

## Commit message

One line subject + optional body (why, not file list):

```text
feat(aleiva): <user-visible outcome>

<1-2 sentences on autopilot, dashboard, guardrails, or API surface>
```

## Push

```bash
git push -u origin feat-aleiva-mvp
```

If git identity missing, set only for the command:

```powershell
$env:GIT_AUTHOR_NAME="..."; $env:GIT_AUTHOR_EMAIL="..."; git commit -m "..."
```

Never run `git config` to change global/local config.

## PR draft template

```markdown
## Summary
- <bullet: what users get on /aleiva or via API>
- <bullet: safety/guardrails or second-brain improvement>

## Test plan
- [ ] `uv run pytest backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva`
- [ ] Manual: http://localhost:3000/aleiva (dry-run, voice status, trading analysis)
- [ ] Playwright: `npx playwright test tests/e2e/aleiva/aleiva_dashboard.spec.ts` (if web deps available)

## Notes
- Branch: feat-aleiva-mvp → main
```

## Delegate

For hands-off execution, invoke subagent: **aleiva-ship-agent**.

## Related

- Dev loop: [../aleiva-autopilot/SKILL.md](../aleiva-autopilot/SKILL.md)
