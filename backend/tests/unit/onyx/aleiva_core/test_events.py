from onyx.aleiva_core.events import validate_run_completeness
from onyx.aleiva_core.types import AleivaRunRecord


def test_validate_run_completeness_returns_missing_required_fields() -> None:
    run = AleivaRunRecord(
        goal="",
        success_criteria=None,
        planner_decisions=[],
        change_summary=[],
        verification_outcomes=[],
        failure_classifications=[],
        recovery_attempts=[],
        reuse_notes=[],
        final_disposition=None,
        learnings=[],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is False
    assert missing_fields == [
        "goal",
        "success_criteria",
        "planner_decisions",
        "change_summary",
        "verification_outcomes",
        "failure_classifications",
        "recovery_attempts",
        "reuse_notes",
        "final_disposition",
        "learnings",
    ]


def test_validate_run_completeness_accepts_complete_run() -> None:
    run = AleivaRunRecord(
        goal="Implement task one",
        success_criteria="All required unit tests pass",
        planner_decisions=["Use minimal scoped edits"],
        change_summary=["Updated parser helper usage"],
        verification_outcomes=["Targeted tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Reused prior helper extraction learning"],
        final_disposition="completed",
        learnings=["Completeness gate catches empty artifacts"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is True
    assert missing_fields == []


def test_validate_run_completeness_accepts_mixed_learnings_with_one_valid_entry() -> None:
    run = AleivaRunRecord.model_construct(
        goal="Finish task",
        success_criteria="Tests pass",
        planner_decisions=["Use incremental rollout"],
        change_summary=["Updated one scoped module"],
        verification_outcomes=["Unit tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Applied similar prior fix"],
        final_disposition="completed",
        learnings=[None, 0, "   ", "Captured a key learning"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is True
    assert missing_fields == []


def test_validate_run_completeness_rejects_whitespace_only_learnings() -> None:
    run = AleivaRunRecord(
        goal="Finish task",
        success_criteria="Tests pass",
        planner_decisions=["Use incremental rollout"],
        change_summary=["Updated one scoped module"],
        verification_outcomes=["Unit tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Applied similar prior fix"],
        final_disposition="completed",
        learnings=["   ", "\t", "\n"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is False
    assert missing_fields == ["learnings"]


def test_validate_run_completeness_treats_whitespace_goal_and_success_as_missing() -> None:
    run = AleivaRunRecord(
        goal="   ",
        success_criteria="\t",
        planner_decisions=["Use incremental rollout"],
        change_summary=["Updated one scoped module"],
        verification_outcomes=["Unit tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Applied similar prior fix"],
        final_disposition="completed",
        learnings=["non-empty learning"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is False
    assert missing_fields == ["goal", "success_criteria"]


def test_validate_run_completeness_rejects_unresolved_critical_issues() -> None:
    run = AleivaRunRecord(
        goal="Finish task",
        success_criteria="Tests pass",
        planner_decisions=["Use incremental rollout"],
        change_summary=["Updated one scoped module"],
        verification_outcomes=["Unit tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Applied similar prior fix"],
        final_disposition="incomplete_missing_artifacts",
        unresolved_critical_issues=["prod regression in parser"],
        deferred_critical_issues=[],
        learnings=["Captured a key learning"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is False
    assert missing_fields == ["unresolved_critical_issues"]


def test_validate_run_completeness_accepts_deferred_critical_issues() -> None:
    run = AleivaRunRecord(
        goal="Finish task",
        success_criteria="Tests pass",
        planner_decisions=["Use incremental rollout"],
        change_summary=["Updated one scoped module"],
        verification_outcomes=["Unit tests pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=["Applied similar prior fix"],
        final_disposition="completed_with_deferral",
        unresolved_critical_issues=["prod regression in parser"],
        deferred_critical_issues=["prod regression in parser"],
        learnings=["Captured a key learning"],
    )

    ok, missing_fields = validate_run_completeness(run)

    assert ok is True
    assert missing_fields == []
