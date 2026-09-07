from onyx.aleiva_core.orchestrator import AleivaRunResult
from onyx.server.features.aleiva.models import AleivaDryRunExplainability
from onyx.server.features.aleiva.models import AleivaMemoryHygieneActionDetail
from onyx.server.features.aleiva.models import AleivaPriorityScoreDetail


def build_dry_run_explainability(
    *,
    goal: str,
    policy_tier: str,
    result: AleivaRunResult,
) -> AleivaDryRunExplainability:
    return AleivaDryRunExplainability(
        goal=goal,
        policy_tier=result.policy_tier or policy_tier,
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
