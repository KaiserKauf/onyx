# Aleiva Autopilot Reference

## Module map

| Path | Role |
|------|------|
| `backend/onyx/aleiva_core/orchestrator.py` | plan → execute → verify → learn |
| `backend/onyx/aleiva_core/controller.py` | autopilot queue + processing |
| `backend/onyx/aleiva_core/policy.py` | guardrails + risk tiers |
| `backend/onyx/aleiva_core/second_brain/` | store, graph, hygiene, decay |
| `backend/onyx/server/features/aleiva/api.py` | FastAPI routes |
| `web/src/app/aleiva/` | Matrix dashboard |
| `.aleiva/` | runtime state (repo root) |

## API endpoints (BFF: `/api/aleiva/...`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/runs/dry` | Dry-run with explainability |
| POST | `/runs` | Execute run |
| GET | `/runs/status` | Queue + KPI snapshot |
| POST | `/autopilot/run` | Process autopilot queue |
| POST | `/memory/hygiene` | Second-brain cleanup |
| POST | `/voice/control` | Voice intents (start/pause/status/report) |
| POST | `/trading/analysis` | Non-execution analysis only |

## Policy tiers

`safe` | `normal` | `experimental` — configured in `backend/onyx/aleiva_core/policy_config.json`

## Project subagents (`.cursor/agents/`)

- `aleiva-orchestrator.md`
- `aleiva-spec-guardian.md`
- `aleiva-quality-reviewer.md`
- `aleiva-frontend-builder.md`
- `aleiva-memory-curator.md`
- `aleiva-e2e-validator.md`
- `aleiva-ship-agent.md`

## Invoke examples

```text
Use the aleiva-autopilot skill and aleiva-orchestrator to continue feat-aleiva-mvp
```

```text
Use aleiva-ship-agent to commit and push Aleiva changes after tests pass
```
