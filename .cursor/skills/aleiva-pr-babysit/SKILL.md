---
name: aleiva-pr-babysit
description: Babysits KaiserKauf/onyx Aleiva pull requests on feat-aleiva-mvp — triages Kilo/review threads, syncs main, fixes in-scope CI, and reports merge-ready status. Use when babysitting a PR, fixing PR checks, or after opening an Aleiva PR.
disable-model-invocation: true
---

# Aleiva PR Babysit

Keep Aleiva PRs merge-ready without weakening CI or gaming bots.

## When to use

- User says: babysit PR, merge-ready, fix CI, Kilo review, PR #2
- After `aleiva-ship` push when checks or review threads need follow-up
- Before merging `feat-aleiva-mvp` → `main`

## Quick start

```powershell
cd .worktrees/a
git fetch origin
gh pr view --repo KaiserKauf/onyx
gh pr checks <n> --repo KaiserKauf/onyx
```

Delegate hands-off triage to subagent: **aleiva-pr-babysitter**.

## Checklist

```text
- [ ] Identify PR number/URL on KaiserKauf/onyx
- [ ] Record mergeable + mergeStateStatus
- [ ] List failing/pending checks
- [ ] Triage unresolved review threads (stale vs valid)
- [ ] Merge origin/main if branch behind (resolve Aleiva-scope conflicts only)
- [ ] Fix in-scope failures; re-run local preflight
- [ ] Push head branch; re-watch checks
- [ ] Verdict: MERGE READY or BLOCKED + next step
```

## In-scope paths

Same as [aleiva-ship](../aleiva-ship/SKILL.md), plus:

- `backend/onyx/background/celery/tasks/aleiva/**`
- `backend/tests/unit/onyx/background/celery/tasks/aleiva/**`
- `.cursor/agents/aleiva-*.md`, `.cursor/skills/aleiva-*/`

## Local preflight (after fixes)

```bash
uv run python -m pytest backend/tests/unit/onyx/aleiva_core backend/tests/unit/server/features/aleiva backend/tests/unit/onyx/background/celery/tasks/aleiva -q
uv run ruff check backend/onyx/aleiva_core backend/onyx/server/features/aleiva backend/onyx/background/celery/tasks/aleiva
```

## Blocking vs non-blocking

| Usually blocking | Often non-blocking |
|------------------|-------------------|
| pytest / Ruff on PR diff | Vercel "deployment blocked" (policy) |
| Required GitHub Actions | Optional bot noise |
| Merge conflicts | Stale bot comment on old SHA |

## Output template

```markdown
## PR
- URL: ...
- Merge: MERGEABLE | CONFLICTING | UNSTABLE — reason

## CI
| Check | Status |
|-------|--------|
| ... | pass/fail/pending |

## Review
- Unresolved threads: N — actions taken

## Pushed
- SHAs: ...

## Verdict
**MERGE READY** | **BLOCKED** — next step
```

## Constraints

- No `git config` changes; no force-push unless user asks
- No commit unless user asks (push existing fix commits is OK)
- Do not skip hooks or weaken workflows to pass checks
- Vulty/trading PRs: use that repo's babysit flow, not this skill

## Related

- Ship: [../aleiva-ship/SKILL.md](../aleiva-ship/SKILL.md)
- Build loop: [../aleiva-autopilot/SKILL.md](../aleiva-autopilot/SKILL.md)
- gh details: [reference.md](reference.md)
