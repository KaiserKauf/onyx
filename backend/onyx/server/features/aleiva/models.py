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
    platform_id: str | None = None


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


class AleivaProbeTargetSummary(BaseModel):
    label: str
    url: str
    kind: Literal["http", "websocket"] = "http"


class AleivaPlatformSummary(BaseModel):
    id: str
    display_name: str
    domains: list[str]
    product_type: str
    risk_level: Literal["low", "medium", "high"]
    capabilities: list[str]
    allowed_actions: list[str]
    control_surface_url: str | None = None
    probe_targets: list[AleivaProbeTargetSummary]


class AleivaPlatformGuideResponse(BaseModel):
    platform_id: str
    display_name: str
    risk_level: Literal["low", "medium", "high"]
    control_surface_url: str | None = None
    onboarding_steps: list[str]
    allowed_actions: list[str]
    capabilities: list[str]
    probe_targets: list[AleivaProbeTargetSummary]
    trading_mode: Literal["paper_sandbox_only", "not_applicable"]
    non_advice_notice: str | None = None


class AleivaCodebaseSnapshotRequest(BaseModel):
    platform_id: str | None = None
    run_id: str | None = None
    test_summary: str | None = None


class AleivaCodebaseSnapshotResponse(BaseModel):
    repo_path: str
    branch: str | None
    head_commit: str | None
    is_dirty: bool
    changed_files: list[str]
    run_id: str | None
    platform_id: str | None
    captured_at: float
    test_summary: str | None = None


class AleivaPlatformLearningSummary(BaseModel):
    platform_id: str
    display_name: str
    learning_count: int
    latest_learning: str | None
    run_count: int
    latest_run_disposition: str | None
    latest_snapshot_commit: str | None
    latest_snapshot_dirty: bool | None


class AleivaAgentLearningStatusResponse(BaseModel):
    total_learnings: int
    total_runs: int
    dry_run_persistence: str
    platforms: list[AleivaPlatformLearningSummary]
    latest_snapshots: list[AleivaCodebaseSnapshotResponse]


class AleivaMemoryIngestRequest(BaseModel):
    topic: str = Field(min_length=1)
    learning: str = Field(min_length=1)
    platform_id: str | None = None
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
