# Aleiva PR Babysit — Reference

## Repo

- Remote: `KaiserKauf/onyx`
- Head branch: `feat-aleiva-mvp`
- Base: `main`
- Typical PR: https://github.com/KaiserKauf/onyx/pull/2

## gh commands

```powershell
gh pr list --repo KaiserKauf/onyx --head feat-aleiva-mvp
gh pr view 2 --repo KaiserKauf/onyx
gh pr checks 2 --repo KaiserKauf/onyx
gh pr checks 2 --repo KaiserKauf/onyx --watch
```

## Sync main into feature branch

```powershell
git fetch origin
git merge origin/main
# resolve conflicts, then:
git push origin feat-aleiva-mvp
```

## Post-merge reminder

If `ALEIVA_MEMORY_HYGIENE_SCHEDULE_ENABLED` is set, operator must restart the Celery **light** worker for beat schedule pickup.

## Subagent coordination

| Need | Delegate |
|------|----------|
| Implement fix | aleiva-orchestrator |
| Spec alignment | aleiva-spec-guardian |
| Quality pass | aleiva-quality-reviewer |
| E2E regression | aleiva-e2e-validator |
| New commit message + push | aleiva-ship-agent |
