import re
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import Field

from onyx.aleiva_core.controller import AleivaAutopilotController
from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.aleiva_core.orchestrator import AleivaRunResult
from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.aleiva_core.second_brain.hygiene import apply_memory_hygiene
from onyx.aleiva_core.second_brain.store import RunArtifactEntry
from onyx.aleiva_core.second_brain.store import SecondBrainStore
from onyx.aleiva_core.trading_analysis import run_trading_analysis_pack
from onyx.aleiva_core.trading_analysis import TradingAnalysisRequest
from onyx.aleiva_core.voice_control import handle_voice_control
from onyx.aleiva_core.voice_control import VoiceControlRequest
from onyx.auth.permissions import require_permission
from onyx.db.enums import Permission
from onyx.db.models import User
from onyx.error_handling.error_codes import OnyxErrorCode
from onyx.error_handling.exceptions import OnyxError

router = APIRouter(prefix="/aleiva")
_ALEIVA_STORE_DIR = Path(__file__).resolve().parents[4] / ".aleiva"
_ALEIVA_QUEUE_DIR = Path(__file__).resolve().parents[4] / ".aleiva"


class AleivaRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    policy_tier: Literal["safe", "normal", "experimental"] = "normal"


class AleivaDryRunExplainability(BaseModel):
    goal: str
    policy_tier: str
    decisions: list[str]
    planned_steps: list[str]
    safety_checks: list[str]
    priority_scores: list[str]
    memory_hygiene_actions: list[str]
    guardrail_events: list[str]
    policy_controls: dict[str, int | str]
    priority_score_details: list["AleivaPriorityScoreDetail"]
    memory_hygiene_action_details: list["AleivaMemoryHygieneActionDetail"]


class AleivaPriorityScoreDetail(BaseModel):
    task: str
    impact: float
    confidence: float
    effort: float
    score: float


class AleivaMemoryHygieneActionDetail(BaseModel):
    action_type: str
    message: str
    topic: str
    learning: str
    contradicted_learning: str | None = None
    previous_confidence: float | None = None
    updated_confidence: float | None = None


class AleivaRunResponse(BaseModel):
    status: str
    lane: str
    plan: list[str]
    execution: list[str]
    verification: list[str]
    learnings: list[str]
    policy_tier: str | None = None
    policy_controls: dict[str, int | str] | None = None
    guardrail_events: list[str] | None = None
    explainability: AleivaDryRunExplainability | None = None


class AleivaQueueSummary(BaseModel):
    queued: int
    running: int
    completed: int
    failed: int
    paused: int


class AleivaMemoryHygieneSummary(BaseModel):
    sampled_entries: int
    action_count: int
    actions: list[str]


class AleivaRunArtifactSummary(BaseModel):
    goal: str
    final_disposition: str
    lane: str
    missing_artifacts: list[str]
    verification_outcomes: list[str]


class AleivaRunStatusResponse(BaseModel):
    queue: AleivaQueueSummary
    latest_runs: list[AleivaRunArtifactSummary]
    memory_hygiene: AleivaMemoryHygieneSummary


class AleivaVoiceControlRequest(BaseModel):
    intent: Literal["start-run", "pause-run", "status", "report"]
    goal: str | None = None
    task_id: str | None = None
    policy_tier: Literal["safe", "normal", "experimental"] = "safe"


class AleivaVoiceControlResponse(BaseModel):
    status: str
    message: str
    queue: AleivaQueueSummary
    enqueued_task_id: str | None = None
    report: dict[str, object] | None = None


class AleivaTradingAnalysisRequest(BaseModel):
    market: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    thesis: str = Field(min_length=1)
    risk_focus: str | None = None


class AleivaTradingAnalysisResponse(BaseModel):
    status: str
    analysis: list[str]
    risk_review: list[str]
    non_execution_safeguards: list[str]
    explainability: dict[str, object]


class AleivaAutopilotRunRequest(BaseModel):
    dry_run: bool = True
    max_iterations: int = Field(default=20, ge=1, le=100)


class AleivaAutopilotCycleSummary(BaseModel):
    task_id: str
    goal: str
    status: str
    reason: str
    run_status: str | None = None


class AleivaAutopilotRunResponse(BaseModel):
    cycles_completed: int
    cycles: list[AleivaAutopilotCycleSummary]
    queue: AleivaQueueSummary


class AleivaMemoryHygieneRunResponse(BaseModel):
    deduplicated_count: int
    decay_action_count: int
    action_count: int
    contradiction_guidance: list[str]
    actions: list[str]


@router.post("/runs/dry")
def run_dry_cycle(
    request: AleivaRunRequest,
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaRunResponse:
    result = _run_cycle_or_raise(
        goal=request.goal,
        dry_run=True,
        policy_tier=request.policy_tier,
        user=user,
    )
    response = AleivaRunResponse.model_validate(result.__dict__)
    response.explainability = AleivaDryRunExplainability(
        goal=request.goal,
        policy_tier=result.policy_tier or request.policy_tier,
        decisions=[
            f"selected lane: {result.lane}",
            "dry-run mode enabled; no mutations executed",
        ],
        planned_steps=[*result.plan, *result.execution, *result.verification],
        safety_checks=[
            "commands validated against allowlist/blocklist policy",
            "mutating operations disabled in dry-run mode",
        ],
        guardrail_events=result.guardrail_events or [],
        policy_controls=result.policy_controls or {},
        priority_scores=[
            f"{entry.task}: {entry.score:.3f}"
            for entry in result.selected_priority_scores
        ],
        memory_hygiene_actions=result.memory_hygiene_actions,
        priority_score_details=[
            AleivaPriorityScoreDetail(
                task=entry.task,
                impact=entry.impact,
                confidence=entry.confidence,
                effort=entry.effort,
                score=entry.score,
            )
            for entry in result.selected_priority_details
        ],
        memory_hygiene_action_details=[
            AleivaMemoryHygieneActionDetail(
                action_type=entry.action_type,
                message=entry.message,
                topic=entry.topic,
                learning=entry.learning,
                contradicted_learning=entry.contradicted_learning,
                previous_confidence=entry.previous_confidence,
                updated_confidence=entry.updated_confidence,
            )
            for entry in result.memory_hygiene_action_details
        ],
    )
    return response


@router.post("/runs")
def run_cycle(
    request: AleivaRunRequest,
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaRunResponse:
    result = _run_cycle_or_raise(
        goal=request.goal,
        dry_run=False,
        policy_tier=request.policy_tier,
        user=user,
    )
    return AleivaRunResponse.model_validate(result.__dict__)


@router.get("/runs/status")
def run_status(
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaRunStatusResponse:
    store = _build_second_brain_store(user=user, dry_run=True, create_if_missing=False)
    queue = _build_task_queue(user=user, create_if_missing=False)

    queue_tasks = queue.list_tasks(limit=200)
    queue_summary = AleivaQueueSummary(
        queued=sum(1 for task in queue_tasks if task.status == "queued"),
        running=sum(1 for task in queue_tasks if task.status == "running"),
        completed=sum(1 for task in queue_tasks if task.status == "completed"),
        failed=sum(1 for task in queue_tasks if task.status == "failed"),
        paused=sum(1 for task in queue_tasks if task.status == "paused"),
    )

    latest_runs = [
        _serialize_run_artifact(entry)
        for entry in store.list_run_artifacts(limit=10)
    ]
    sampled_entries = store.list_learnings(limit=30)
    hygiene = apply_memory_hygiene(sampled_entries)

    return AleivaRunStatusResponse(
        queue=queue_summary,
        latest_runs=latest_runs,
        memory_hygiene=AleivaMemoryHygieneSummary(
            sampled_entries=len(sampled_entries),
            action_count=len(hygiene.actions),
            actions=hygiene.actions,
        ),
    )


@router.post("/autopilot/run")
def run_autopilot(
    request: AleivaAutopilotRunRequest,
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaAutopilotRunResponse:
    queue = _build_task_queue(user=user, create_if_missing=True)
    store = _build_second_brain_store(
        user=user,
        dry_run=request.dry_run,
        create_if_missing=not request.dry_run,
    )
    controller = AleivaAutopilotController(
        queue=queue,
        max_iterations_per_run=request.max_iterations,
    )
    outcomes = controller.run_until_idle(
        dry_run=request.dry_run,
        second_brain_store=store,
    )
    queue_tasks = queue.list_tasks(limit=200)
    return AleivaAutopilotRunResponse(
        cycles_completed=len(outcomes),
        cycles=[
            AleivaAutopilotCycleSummary(
                task_id=result.task.task_id,
                goal=result.task.goal,
                status=result.status,
                reason=result.reason,
                run_status=result.run_result.status if result.run_result else None,
            )
            for result in outcomes
        ],
        queue=AleivaQueueSummary(
            queued=sum(1 for task in queue_tasks if task.status == "queued"),
            running=sum(1 for task in queue_tasks if task.status == "running"),
            completed=sum(1 for task in queue_tasks if task.status == "completed"),
            failed=sum(1 for task in queue_tasks if task.status == "failed"),
            paused=sum(1 for task in queue_tasks if task.status == "paused"),
        ),
    )


@router.post("/memory/hygiene")
def run_memory_hygiene(
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaMemoryHygieneRunResponse:
    try:
        store = _build_second_brain_store(user=user, dry_run=False, create_if_missing=True)
        summary = store.apply_scheduled_hygiene()
    except OSError as exc:
        raise OnyxError(
            OnyxErrorCode.INTERNAL_ERROR,
            "Aleiva memory hygiene storage unavailable",
        ) from exc

    contradiction_guidance = summary.get("contradiction_guidance", [])
    actions = summary.get("actions", [])
    return AleivaMemoryHygieneRunResponse(
        deduplicated_count=int(summary.get("deduplicated_count", 0)),
        decay_action_count=int(summary.get("decay_action_count", 0)),
        action_count=int(summary.get("action_count", 0)),
        contradiction_guidance=(
            [str(item) for item in contradiction_guidance]
            if isinstance(contradiction_guidance, list)
            else []
        ),
        actions=[str(item) for item in actions] if isinstance(actions, list) else [],
    )


@router.post("/voice/control")
def voice_control(
    request: AleivaVoiceControlRequest,
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaVoiceControlResponse:
    queue = _build_task_queue(user=user, create_if_missing=True)
    store = _build_second_brain_store(user=user, dry_run=True, create_if_missing=False)
    response = handle_voice_control(
        VoiceControlRequest(
            intent=request.intent,
            goal=request.goal,
            task_id=request.task_id,
            policy_tier=request.policy_tier,
        ),
        queue=queue,
        second_brain_store=store,
    )
    return AleivaVoiceControlResponse(
        status=response.status,
        message=response.message,
        queue=AleivaQueueSummary(**response.queue),
        enqueued_task_id=response.enqueued_task_id,
        report=response.report,
    )


@router.post("/trading/analysis")
def trading_analysis(
    request: AleivaTradingAnalysisRequest,
    user: User = Depends(require_permission(Permission.BASIC_ACCESS)),
) -> AleivaTradingAnalysisResponse:
    store = _build_second_brain_store(user=user, dry_run=True, create_if_missing=False)
    result = run_trading_analysis_pack(
        TradingAnalysisRequest(
            market=request.market,
            symbol=request.symbol,
            timeframe=request.timeframe,
            thesis=request.thesis,
            risk_focus=request.risk_focus,
        ),
        second_brain_store=store,
    )
    return AleivaTradingAnalysisResponse(
        status=result.status,
        analysis=result.analysis,
        risk_review=result.risk_review,
        non_execution_safeguards=result.non_execution_safeguards,
        explainability=result.explainability,
    )


def _build_second_brain_store(
    user: User,
    dry_run: bool,
    create_if_missing: bool | None = None,
) -> SecondBrainStore:
    user_identifier = str(getattr(user, "id", "anonymous"))
    safe_user_identifier = re.sub(r"[^a-zA-Z0-9_-]", "_", user_identifier)
    should_create = not dry_run if create_if_missing is None else create_if_missing
    return SecondBrainStore(
        _ALEIVA_STORE_DIR / f"second_brain_{safe_user_identifier}.jsonl",
        create_if_missing=should_create,
    )


def _build_task_queue(user: User, create_if_missing: bool) -> AleivaTaskQueue:
    user_identifier = str(getattr(user, "id", "anonymous"))
    safe_user_identifier = re.sub(r"[^a-zA-Z0-9_-]", "_", user_identifier)
    return AleivaTaskQueue(
        _ALEIVA_QUEUE_DIR / f"task_queue_{safe_user_identifier}.json",
        create_if_missing=create_if_missing,
    )


def _serialize_run_artifact(entry: RunArtifactEntry) -> AleivaRunArtifactSummary:
    return AleivaRunArtifactSummary(
        goal=entry.goal,
        final_disposition=entry.final_disposition,
        lane=entry.lane,
        missing_artifacts=entry.missing_artifacts,
        verification_outcomes=entry.verification_outcomes,
    )


def _run_cycle_or_raise(
    goal: str,
    dry_run: bool,
    policy_tier: Literal["safe", "normal", "experimental"],
    user: User,
) -> AleivaRunResult:
    try:
        return run_aleiva_cycle(
            goal=goal,
            dry_run=dry_run,
            policy_tier=policy_tier,
            second_brain_store=_build_second_brain_store(user, dry_run=dry_run),
        )
    except OSError as exc:
        raise OnyxError(
            OnyxErrorCode.INTERNAL_ERROR,
            "Aleiva run storage unavailable",
        ) from exc
