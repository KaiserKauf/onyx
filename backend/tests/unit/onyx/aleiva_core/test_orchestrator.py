from pathlib import Path

from onyx.aleiva_core.eval import choose_lane
from onyx.aleiva_core.orchestrator import apply_flaky_test_rerun_heuristics
from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.aleiva_core.second_brain.store import RunArtifactEntry
from onyx.aleiva_core.second_brain.store import SecondBrainStore


def test_choose_lane_moves_to_stability_when_quality_drops() -> None:
    lane = choose_lane(speed=0.8, quality=0.3, knowledge_reuse=0.7)
    assert lane == "stability_lane"


def test_choose_lane_moves_to_fast_lane_when_all_kpis_are_high() -> None:
    lane = choose_lane(speed=0.9, quality=0.9, knowledge_reuse=0.8)
    assert lane == "fast_lane"


def test_choose_lane_moves_to_stability_when_quality_drift_exceeds_threshold() -> None:
    lane = choose_lane(
        speed=0.9,
        quality=0.72,
        knowledge_reuse=0.8,
        previous_quality=0.92,
    )
    assert lane == "stability_lane"


def test_flaky_test_rerun_heuristics_adds_retry_outcomes() -> None:
    outcomes = apply_flaky_test_rerun_heuristics(
        verification_outcomes=["flaky test failed in integration suite"],
        rerun_limit=2,
    )

    assert "flaky rerun attempt 1: still failing" in outcomes
    assert "flaky rerun attempt 2: passed" in outcomes


def test_run_cycle_records_learning(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=False,
        second_brain_store=store,
    )

    assert result.status == "completed"
    assert result.policy_tier == "normal"
    assert result.policy_controls is not None
    assert result.policy_controls["tier"] == "normal"
    assert result.guardrail_events
    assert result.missing_artifacts == []
    assert len(result.learnings) > 0

    persisted = store.retrieve("Refactor parser", limit=5)
    assert len(persisted) >= 1
    assert any("Prefer small scoped changes" in entry.learning for entry in persisted)

    run_artifacts = store.list_run_artifacts(limit=1)
    assert len(run_artifacts) == 1
    run_artifact = run_artifacts[0]
    assert run_artifact.goal == "Refactor parser"
    assert run_artifact.success_criteria
    assert run_artifact.planner_decisions
    assert run_artifact.change_summary
    assert run_artifact.verification_outcomes
    assert run_artifact.failure_classifications
    assert run_artifact.recovery_attempts
    assert run_artifact.reuse_notes
    assert run_artifact.learnings
    assert run_artifact.final_disposition == "completed"
    assert run_artifact.missing_artifacts == []
    assert run_artifact.relations


def test_run_cycle_dry_run_does_not_persist_entries(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=True,
        second_brain_store=store,
    )

    assert result.status == "completed"
    assert result.policy_tier == "normal"
    assert result.selected_priority_scores
    assert result.selected_priority_details
    assert all(detail.score > 0 for detail in result.selected_priority_details)
    assert result.memory_hygiene_actions
    assert result.memory_hygiene_action_details
    assert store.retrieve("Refactor parser", limit=5) == []
    assert store.list_run_artifacts(limit=5) == []


def test_run_cycle_supports_safe_policy_tier(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=True,
        policy_tier="safe",
        second_brain_store=store,
    )

    assert result.policy_tier == "safe"
    assert result.policy_controls is not None
    assert result.policy_controls["max_commands_per_run"] == 5


def test_run_cycle_marks_incomplete_for_missing_goal_and_persists_disposition(
    tmp_path: Path,
) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    result = run_aleiva_cycle(
        goal="   ",
        dry_run=False,
        second_brain_store=store,
    )

    assert result.status == "incomplete"
    assert "goal" in result.missing_artifacts

    run_artifacts = store.list_run_artifacts(limit=1)
    assert len(run_artifacts) == 1
    assert run_artifacts[0].final_disposition == "incomplete_missing_artifacts"
    assert "goal" in run_artifacts[0].missing_artifacts


def test_run_cycle_marks_incomplete_when_persistence_fails(tmp_path: Path) -> None:
    class FailingStore(SecondBrainStore):
        def append_learning(self, _topic: str, _learning: str, _confidence: float) -> None:
            raise OSError("disk full")

        def append_run_artifact(self, _entry: RunArtifactEntry) -> None:
            raise OSError("disk full")

    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=False,
        second_brain_store=FailingStore(tmp_path / "brain.jsonl"),
    )

    assert result.status == "incomplete"
    assert "persistence_store" in result.missing_artifacts


def test_run_cycle_persists_artifact_even_if_learning_write_fails(tmp_path: Path) -> None:
    class LearningFailStore(SecondBrainStore):
        def append_learning(self, _topic: str, _learning: str, _confidence: float) -> None:
            raise OSError("learning write failed")

    store = LearningFailStore(tmp_path / "brain.jsonl")
    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=False,
        second_brain_store=store,
    )

    assert result.status == "incomplete"
    assert "persistence_store" in result.missing_artifacts

    run_artifacts = store.list_run_artifacts(limit=1)
    assert len(run_artifacts) == 1
    assert run_artifacts[0].final_disposition == "incomplete_missing_artifacts"
