from onyx.aleiva_core.orchestrator import AleivaRunResult
from onyx.aleiva_core.prioritization import PriorityScore
from onyx.aleiva_core.roi_priority import RoiPriorityScore
from onyx.aleiva_core.second_brain.hygiene import MemoryHygieneAction
from onyx.server.features.aleiva.explainability import build_dry_run_explainability


def test_build_dry_run_explainability_maps_run_result_fields() -> None:
    result = AleivaRunResult(
        status="completed",
        lane="balanced",
        plan=["Plan task"],
        execution=["dry-run execution"],
        verification=["quick checks pass"],
        learnings=["Prefer small scoped changes"],
        missing_artifacts=[],
        selected_priority_scores=[PriorityScore(task="plan", score=0.8)],
        selected_priority_details=[
            RoiPriorityScore(
                task="plan",
                impact=0.8,
                confidence=0.9,
                effort=1.0,
                score=0.72,
            )
        ],
        memory_hygiene_actions=["noop"],
        memory_hygiene_action_details=[
            MemoryHygieneAction(
                action_type="noop",
                message="no actions",
                topic="",
                learning="",
            )
        ],
        policy_tier="normal",
        policy_controls={"tier": "normal"},
        guardrail_events=["allowlisted verification command"],
    )

    explainability = build_dry_run_explainability(
        goal="Refactor parser",
        policy_tier="normal",
        result=result,
    )

    assert explainability.goal == "Refactor parser"
    assert explainability.policy_tier == "normal"
    assert any("dry-run mode" in decision for decision in explainability.decisions)
    assert explainability.planned_steps
    assert explainability.priority_score_details[0].task == "plan"
    assert explainability.memory_hygiene_action_details[0].action_type == "noop"
