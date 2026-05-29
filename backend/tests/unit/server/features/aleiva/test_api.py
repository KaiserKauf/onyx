from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.error_handling.exceptions import register_onyx_exception_handlers
from onyx.main import get_application
from onyx.server.features.aleiva import api as aleiva_api_module
from onyx.server.features.aleiva.api import router as aleiva_router


@asynccontextmanager
async def _noop_lifespan(_: object) -> AsyncGenerator[None, None]:
    yield


def test_aleiva_run_dry_endpoint_returns_completed() -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        if getattr(route, "path", "") != "/api/aleiva/runs/dry":
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    client = TestClient(app)
    response = client.post("/api/aleiva/runs/dry", json={"goal": "Refactor parser"})

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["execution"] == ["dry-run execution"]
    explainability = response.json()["explainability"]
    assert explainability["goal"] == "Refactor parser"
    assert any(
        "no mutations executed" in decision for decision in explainability["decisions"]
    )
    assert explainability["planned_steps"]
    assert explainability["safety_checks"]
    assert explainability["policy_tier"] == "normal"
    assert explainability["guardrail_events"]
    assert explainability["policy_controls"]["tier"] == "normal"
    assert explainability["priority_scores"]
    assert explainability["memory_hygiene_actions"]
    assert explainability["priority_score_details"]
    assert explainability["memory_hygiene_action_details"]


def test_aleiva_dry_run_does_not_create_store_files(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        if getattr(route, "path", "") != "/api/aleiva/runs/dry":
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post("/api/aleiva/runs/dry", json={"goal": "Refactor parser"})

    assert response.status_code == 200
    assert not (tmp_path / "aleiva").exists()


def test_aleiva_dry_run_returns_controlled_error_when_store_unavailable() -> None:
    app = FastAPI()
    register_onyx_exception_handlers(app)
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        if getattr(route, "path", "") != "/api/aleiva/runs/dry":
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(
        aleiva_api_module,
        "_build_second_brain_store",
        side_effect=OSError("permission denied"),
    ):
        client = TestClient(app)
        response = client.post("/api/aleiva/runs/dry", json={"goal": "Refactor parser"})

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "INTERNAL_ERROR"
    assert "storage unavailable" in body["detail"].lower()


def test_main_wires_aleiva_router() -> None:
    app = get_application(lifespan_override=_noop_lifespan)
    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/aleiva/runs/dry" in route_paths or "/api/aleiva/runs/dry" in route_paths
    assert "/aleiva/runs" in route_paths or "/api/aleiva/runs" in route_paths


def test_aleiva_status_endpoint_exposes_dashboard_fields(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"), patch.object(
        aleiva_api_module, "_ALEIVA_QUEUE_DIR", tmp_path / "aleiva"
    ):
        queue = AleivaTaskQueue(tmp_path / "aleiva" / "task_queue_anonymous.json")
        queue.enqueue("Queue task for dashboard")
        client = TestClient(app)
        run_response = client.post("/api/aleiva/runs", json={"goal": "Refactor parser"})
        assert run_response.status_code == 200

        response = client.get("/api/aleiva/runs/status")

    assert response.status_code == 200
    body = response.json()
    assert body["queue"]["queued"] >= 1
    assert body["memory_hygiene"]["sampled_entries"] >= 1
    assert body["memory_hygiene"]["actions"]
    assert body["latest_runs"]


def test_aleiva_voice_control_endpoint_handles_start_and_status(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"), patch.object(
        aleiva_api_module, "_ALEIVA_QUEUE_DIR", tmp_path / "aleiva"
    ):
        client = TestClient(app)
        start_response = client.post(
            "/api/aleiva/voice/control",
            json={"intent": "start-run", "goal": "Refactor parser"},
        )
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "accepted"
        assert start_response.json()["queue"]["queued"] >= 1

        status_response = client.post("/api/aleiva/voice/control", json={"intent": "status"})

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "accepted"


def test_aleiva_trading_analysis_endpoint_is_analysis_only(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post(
            "/api/aleiva/trading/analysis",
            json={
                "market": "crypto",
                "symbol": "BTCUSD",
                "timeframe": "4h",
                "thesis": "bullish continuation after consolidation",
                "risk_focus": "liquidity shock risk",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "analysis_only"
    assert body["analysis"]
    assert body["risk_review"]
    assert any("disallowed" in item for item in body["non_execution_safeguards"])
    assert body["explainability"]["execution_enabled"] is False


def test_aleiva_autopilot_run_endpoint_processes_queued_tasks(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"), patch.object(
        aleiva_api_module, "_ALEIVA_QUEUE_DIR", tmp_path / "aleiva"
    ):
        queue = AleivaTaskQueue(tmp_path / "aleiva" / "task_queue_anonymous.json")
        queue.enqueue("Refactor parser")
        client = TestClient(app)
        response = client.post("/api/aleiva/autopilot/run", json={"dry_run": True})

    assert response.status_code == 200
    body = response.json()
    assert body["cycles_completed"] == 1
    assert body["cycles"][0]["status"] == "completed"
    assert body["queue"]["completed"] >= 1


def test_aleiva_memory_hygiene_endpoint_runs_scheduled_hygiene(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/aleiva/"):
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post("/api/aleiva/memory/hygiene")

    assert response.status_code == 200
    body = response.json()
    assert "deduplicated_count" in body
    assert "action_count" in body
    assert isinstance(body["actions"], list)


def test_aleiva_run_endpoint_respects_policy_tier(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        if getattr(route, "path", "") != "/api/aleiva/runs":
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post(
            "/api/aleiva/runs",
            json={"goal": "Refactor parser", "policy_tier": "experimental"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["policy_tier"] == "experimental"


def test_aleiva_memory_hygiene_endpoint_returns_error_when_store_unavailable() -> None:
    app = FastAPI()
    register_onyx_exception_handlers(app)
    app.include_router(aleiva_router, prefix="/api")
    for route in app.routes:
        if getattr(route, "path", "") != "/api/aleiva/memory/hygiene":
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()

    with patch.object(
        aleiva_api_module,
        "_build_second_brain_store",
        side_effect=OSError("permission denied"),
    ):
        client = TestClient(app)
        response = client.post("/api/aleiva/memory/hygiene")

    assert response.status_code == 500
    body = response.json()
    assert body["error_code"] == "INTERNAL_ERROR"
    assert "storage unavailable" in body["detail"].lower()


def test_aleiva_core_public_exports_are_importable() -> None:
    from onyx import aleiva_core

    assert aleiva_core.run_aleiva_cycle is not None
    assert aleiva_core.SecondBrainStore is not None
    assert "run_aleiva_cycle" in aleiva_core.__all__
