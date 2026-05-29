import pytest

from onyx.aleiva_core.roi_priority import rank_tasks_by_roi
from onyx.aleiva_core.roi_priority import RoiTaskCandidate
from onyx.aleiva_core.roi_priority import score_roi_task


def test_score_roi_task_returns_full_scoring_details() -> None:
    scored = score_roi_task(
        RoiTaskCandidate(
            task="run focused validations",
            impact=0.9,
            confidence=0.8,
            effort=1.2,
        )
    )

    assert scored.task == "run focused validations"
    assert scored.impact == pytest.approx(0.9)
    assert scored.confidence == pytest.approx(0.8)
    assert scored.effort == pytest.approx(1.2)
    assert scored.score == pytest.approx(0.6)


def test_score_roi_task_rejects_non_positive_effort() -> None:
    with pytest.raises(ValueError, match="effort must be greater than 0"):
        score_roi_task(
            RoiTaskCandidate(
                task="persist artifacts",
                impact=0.8,
                confidence=0.9,
                effort=0.0,
            )
        )


def test_rank_tasks_by_roi_orders_by_descending_score() -> None:
    ranked = rank_tasks_by_roi(
        [
            RoiTaskCandidate(
                task="persist run artifacts",
                impact=0.7,
                confidence=0.8,
                effort=1.0,
            ),
            RoiTaskCandidate(
                task="plan scoped implementation",
                impact=0.9,
                confidence=0.9,
                effort=1.1,
            ),
            RoiTaskCandidate(
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
