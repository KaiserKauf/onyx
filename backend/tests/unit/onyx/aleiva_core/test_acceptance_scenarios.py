"""Aleiva MVP acceptance scenarios — safe dry-run based validation.

These scenarios document the three acceptance-run paths from the Aleiva hybrid
MVP design. Each scenario runs entirely in dry-run mode with isolated storage.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.aleiva_core.second_brain.store import SecondBrainStore
from onyx.error_handling.exceptions import register_onyx_exception_handlers
from onyx.server.features.aleiva import api as aleiva_api_module
from onyx.server.features.aleiva.api import router as aleiva_router


def _build_test_client(tmp_path: Path) -> TestClient:
    app = FastAPI()
    register_onyx_exception_handlers(app)
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    store_patch = patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva")
    queue_patch = patch.object(aleiva_api_module, "_ALEIVA_QUEUE_DIR", tmp_path / "aleiva")
    store_patch.start()
    queue_patch.start()
    return TestClient(app)


@pytest.mark.parametrize(
    ("scenario_name", "goal", "policy_tier"),
    [
        (
            "code_autopilot_refactor",
            "Refactor parser module with focused unit tests",
            "normal",
        ),
        (
            "second_brain_hygiene_audit",
            "Audit second-brain learnings and apply hygiene guidance",
            "safe",
        ),
        (
            "integration_coverage_expansion",
            "Add integration coverage for Aleiva API endpoints",
            "experimental",
        ),
    ],
)
def test_acceptance_scenario_dry_run_via_api(
    tmp_path: Path,
    scenario_name: str,
    goal: str,
    policy_tier: str,
) -> None:
    """Scenario: dry-run cycle completes with explainability and guardrails."""
    client = _build_test_client(tmp_path)

    response = client.post(
        "/api/aleiva/runs/dry",
        json={"goal": goal, "policy_tier": policy_tier},
    )

    assert response.status_code == 200, scenario_name
    body = response.json()
    assert body["status"] == "completed"
    assert body["explainability"]["goal"] == goal
    assert body["explainability"]["policy_tier"] == policy_tier
    assert body["explainability"]["safety_checks"]
    assert body["explainability"]["guardrail_events"] is not None
    assert any(
        "no mutations executed" in decision.lower()
        for decision in body["explainability"]["decisions"]
    )


def test_acceptance_scenario_queue_and_autopilot_dry_run(tmp_path: Path) -> None:
    """Scenario: enqueue work, process via autopilot dry-run, verify queue state."""
    client = _build_test_client(tmp_path)
    queue = AleivaTaskQueue(tmp_path / "aleiva" / "task_queue_anonymous.json")
    queue.enqueue("Refactor parser module with focused unit tests")

    autopilot_response = client.post(
        "/api/aleiva/autopilot/run",
        json={"dry_run": True, "max_iterations": 5},
    )

    assert autopilot_response.status_code == 200
    autopilot_body = autopilot_response.json()
    assert autopilot_body["cycles_completed"] >= 1
    assert autopilot_body["queue"]["completed"] >= 1

    status_response = client.get("/api/aleiva/runs/status")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["memory_hygiene"]["sampled_entries"] >= 0


def test_acceptance_scenario_orchestrator_persists_artifacts(tmp_path: Path) -> None:
    """Scenario: live cycle (non-dry) persists second-brain artifacts for reuse."""
    store_path = tmp_path / "aleiva" / "second_brain_acceptance.jsonl"
    store = SecondBrainStore(store_path, create_if_missing=True)

    result = run_aleiva_cycle(
        goal="Document acceptance scenarios for dry-run validation",
        dry_run=False,
        policy_tier="safe",
        second_brain_store=store,
    )

    assert result.status == "completed"
    artifacts = store.list_run_artifacts(limit=5)
    assert artifacts
    assert artifacts[0].goal == "Document acceptance scenarios for dry-run validation"
