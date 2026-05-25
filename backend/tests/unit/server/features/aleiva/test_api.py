from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from onyx.main import get_application
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


def test_main_wires_aleiva_router() -> None:
    app = get_application(lifespan_override=_noop_lifespan)
    route_paths = {getattr(route, "path", "") for route in app.routes}
    assert "/aleiva/runs/dry" in route_paths or "/api/aleiva/runs/dry" in route_paths
    assert "/aleiva/runs" in route_paths or "/api/aleiva/runs" in route_paths
