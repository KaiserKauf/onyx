from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field

from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.auth.permissions import require_permission
from onyx.db.enums import Permission
from onyx.db.models import User

router = APIRouter(prefix="/aleiva")


class AleivaRunRequest(BaseModel):
    goal: str = Field(min_length=1)


class AleivaRunResponse(BaseModel):
    status: str
    lane: str
    plan: list[str]
    execution: list[str]
    verification: list[str]
    learnings: list[str]


@router.post("/runs/dry")
def run_dry_cycle(
    request: AleivaRunRequest,
    _: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaRunResponse:
    result = run_aleiva_cycle(goal=request.goal, dry_run=True)
    return AleivaRunResponse.model_validate(result.__dict__)


@router.post("/runs")
def run_cycle(
    request: AleivaRunRequest,
    _: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaRunResponse:
    result = run_aleiva_cycle(goal=request.goal, dry_run=False)
    return AleivaRunResponse.model_validate(result.__dict__)
