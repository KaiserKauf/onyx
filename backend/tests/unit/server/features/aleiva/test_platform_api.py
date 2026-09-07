from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from onyx.error_handling.exceptions import register_onyx_exception_handlers
from onyx.server.features.aleiva import api as aleiva_api_module
from onyx.server.features.aleiva.api import router as aleiva_router


def _override_auth(app: FastAPI, path: str) -> None:
    for route in app.routes:
        if getattr(route, "path", "") != path:
            continue
        for dependency in route.dependant.dependencies:
            app.dependency_overrides[dependency.cache_key[0]] = lambda: object()


def test_list_platforms_endpoint() -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/platforms")

    client = TestClient(app)
    response = client.get("/api/aleiva/platforms")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert {entry["id"] for entry in payload} == {
        "aleivaos",
        "vulty",
        "aleiva-music",
        "aleiva-quantum-trading",
    }


def test_platform_guide_endpoint() -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/platforms/{platform_id}/guide")

    client = TestClient(app)
    response = client.get("/api/aleiva/platforms/vulty/guide")

    assert response.status_code == 200
    payload = response.json()
    assert payload["platform_id"] == "vulty"
    assert payload["trading_mode"] == "paper_sandbox_only"
    assert payload["onboarding_steps"]


def test_platform_guide_not_found() -> None:
    app = FastAPI()
    register_onyx_exception_handlers(app)
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/platforms/{platform_id}/guide")

    client = TestClient(app)
    response = client.get("/api/aleiva/platforms/does-not-exist/guide")

    assert response.status_code == 404


def test_agent_learning_status_endpoint(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/agents/learning/status")

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.get("/api/aleiva/agents/learning/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run_persistence"] == "disabled_by_design"
    assert len(payload["platforms"]) == 4


def test_codebase_snapshot_endpoint(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/codebase/snapshot")

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post(
            "/api/aleiva/codebase/snapshot",
            json={"platform_id": "aleivaos", "run_id": "manual-snapshot"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["platform_id"] == "aleivaos"
    assert payload["run_id"] == "manual-snapshot"


def test_memory_ingest_endpoint(tmp_path: Path) -> None:
    app = FastAPI()
    app.include_router(aleiva_router, prefix="/api")
    _override_auth(app, "/api/aleiva/memory/ingest")

    with patch.object(aleiva_api_module, "_ALEIVA_STORE_DIR", tmp_path / "aleiva"):
        client = TestClient(app)
        response = client.post(
            "/api/aleiva/memory/ingest",
            json={
                "topic": "operator note",
                "learning": "Jarvis bridge must run on :8900 for Claw3D probes",
                "platform_id": "aleivaos",
                "confidence": 0.8,
            },
        )

    assert response.status_code == 200
    assert response.json()["action_count"] == 1
