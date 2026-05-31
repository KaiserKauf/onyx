from typing import Literal

from pydantic import BaseModel
from pydantic import Field


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
    priority_score_details: list[AleivaPriorityScoreDetail]
    memory_hygiene_action_details: list[AleivaMemoryHygieneActionDetail]


class AleivaRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    policy_tier: Literal["safe", "normal", "experimental"] = "normal"


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


class AleivaKpiSnapshot(BaseModel):
    speed: float
    quality: float
    knowledge_reuse: float
    lane: str


class AleivaKpiTrendPoint(BaseModel):
    run_index: int
    goal: str
    speed: float
    quality: float
    knowledge_reuse: float
    lane: str


class AleivaKpiTrendsSummary(BaseModel):
    current: AleivaKpiSnapshot
    trend: Literal["improving", "stable", "declining"]
    points: list[AleivaKpiTrendPoint]


class AleivaRunStatusResponse(BaseModel):
    queue: AleivaQueueSummary
    latest_runs: list[AleivaRunArtifactSummary]
    memory_hygiene: AleivaMemoryHygieneSummary
    kpi_trends: AleivaKpiTrendsSummary | None = None


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
