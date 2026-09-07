# Aleiva Memory Hygiene — Reference

## Modules

| File | Role |
|------|------|
| `backend/onyx/aleiva_core/second_brain/hygiene.py` | `apply_memory_hygiene`, scheduled summary types |
| `backend/onyx/aleiva_core/second_brain/contradiction_decay.py` | Decay + contradiction actions |
| `backend/onyx/aleiva_core/second_brain/store.py` | JSONL persistence, `apply_scheduled_hygiene()` |
| `backend/onyx/aleiva_core/events.py` | `validate_run_completeness` (non-forgetting gate) |
| `backend/onyx/background/celery/tasks/aleiva/tasks.py` | `aleiva_memory_hygiene_task` |

## Storage

- Directory: `backend/.aleiva/` (resolved from API module parents)
- Per user: `second_brain_<safe_user_id>.jsonl`

## API

- Route: `POST /aleiva/memory/hygiene` (BFF: `/api/aleiva/memory/hygiene`)
- Response model: `AleivaMemoryHygieneRunResponse` in `server/features/aleiva/models.py`
- Errors: `OnyxError` only

## Manual smoke (via BFF)

```bash
# Requires logged-in session cookie or test harness; prefer Playwright panel when available.
curl -s -X POST http://localhost:3000/api/aleiva/memory/hygiene -H "Content-Type: application/json"
```

## Celery manual enqueue

```python
from onyx.background.celery.tasks.aleiva.tasks import aleiva_memory_hygiene_task
aleiva_memory_hygiene_task.apply_async(expires=900)
```

## Explainability

Dry-run explainability may surface `memory_hygiene_actions` and `memory_hygiene_action_details` — keep in sync with `MemoryHygieneAction` in `contradiction_decay.py`.
