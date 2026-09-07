import pytest

from onyx.aleiva_core.prioritization import calculate_roi_priority
from onyx.aleiva_core.prioritization import prioritize_tasks
from onyx.aleiva_core.prioritization import PriorityCandidate


def test_calculate_roi_priority_uses_impact_confidence_over_effort() -> None:
    score = calculate_roi_priority(
        PriorityCandidate(
            task="run focused validations",
            impact=0.9,
            confidence=0.8,
            effort=1.2,
        )
    )

    assert score.task == "run focused validations"
    assert score.score == pytest.approx(0.6)


def test_calculate_roi_priority_rejects_non_positive_effort() -> None:
    with pytest.raises(ValueError, match="effort must be greater than 0"):
        calculate_roi_priority(
            PriorityCandidate(
                task="persist artifacts",
                impact=0.7,
                confidence=0.9,
                effort=0.0,
            )
        )


def test_prioritize_tasks_orders_by_descending_score() -> None:
    ranked = prioritize_tasks(
        [
            PriorityCandidate(
                task="persist run artifacts",
                impact=0.7,
                confidence=0.8,
                effort=1.0,
            ),
            PriorityCandidate(
                task="plan scoped implementation",
                impact=0.9,
                confidence=0.9,
                effort=1.1,
            ),
            PriorityCandidate(
                task="run focused validations",
                impact=0.95,
                confidence=0.95,
                effort=1.5,
            ),
        ]
    )

    assert [entry.task for entry in ranked] == [
        "plan scoped implementation",
        "run focused validations",
        "persist run artifacts",
    ]
