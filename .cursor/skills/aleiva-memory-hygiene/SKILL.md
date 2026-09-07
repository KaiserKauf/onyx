---
name: aleiva-memory-hygiene
description: Runs Aleiva second-brain hygiene (dedup, decay, contradiction tagging) via API, store, or opt-in Celery beat. Use when curating learnings, enabling scheduled hygiene, or debugging memory quality on feat-aleiva-mvp.
disable-model-invocation: true
---

# Aleiva Memory Hygiene

Keeps `.aleiva/` second-brain stores accurate without dropping required run artifacts.

## When to use

- User mentions memory hygiene, dedup, decay, contradictions, second brain cleanup
- After autonomous runs that add many learnings
- Enabling or testing `ALEIVA_MEMORY_HYGIENE_SCHEDULE_ENABLED`
- Dashboard or API hygiene actions look stale or noisy

## Quick paths

| Trigger | How |
|---------|-----|
| Manual (user) | `POST /api/aleiva/memory/hygiene` via frontend or curl through `:3000` |
| In-process | `SecondBrainStore.apply_scheduled_hygiene()` |
| Scheduled | Celery `aleiva_memory_hygiene_task` (beat, opt-in) |

Delegate deep curation to subagent **aleiva-memory-curator**.

## Checklist

```text
- [ ] Read current store: .aleiva/second_brain_<user>.jsonl
- [ ] Run unit tests for hygiene modules
- [ ] Apply or verify hygiene (API or store method)
- [ ] Confirm completeness gate still passes on sample runs
- [ ] Document env change if beat enabled (restart light worker)
```

## Verify

```bash
uv run python -m pytest backend/tests/unit/onyx/aleiva_core/test_memory_hygiene.py backend/tests/unit/onyx/aleiva_core/test_contradiction_decay.py backend/tests/unit/onyx/aleiva_core/test_second_brain_store.py backend/tests/unit/onyx/background/celery/tasks/aleiva/test_tasks.py -q
uv run ruff check backend/onyx/aleiva_core/second_brain backend/onyx/background/celery/tasks/aleiva
```

## Rules

- Do not delete learnings without decay/contradiction policy justification.
- Tag contradictions; never auto-apply conflicting learnings to planner decisions.
- Completeness gate (`validate_run_completeness`) is separate — hygiene does not excuse missing run artifacts.

## Enable Celery beat (optional)

```text
ALEIVA_MEMORY_HYGIENE_SCHEDULE_ENABLED=true
```

Then restart the Celery **light** worker. Task name: `OnyxCeleryTask.ALEIVA_MEMORY_HYGIENE_TASK`.

## Related

- Modules and API: [reference.md](reference.md)
- Build loop: [../aleiva-autopilot/SKILL.md](../aleiva-autopilot/SKILL.md)
