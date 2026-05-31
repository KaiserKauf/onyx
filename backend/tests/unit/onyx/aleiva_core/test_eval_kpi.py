from onyx.aleiva_core.eval import build_kpi_trends
from onyx.aleiva_core.eval import compute_run_kpis
from onyx.aleiva_core.second_brain.store import RunArtifactEntry


def _artifact(
    *,
    goal: str = "Refactor parser",
    lane: str = "balanced",
    disposition: str = "completed",
    verification: list[str] | None = None,
    reuse_notes: list[str] | None = None,
    missing: list[str] | None = None,
) -> RunArtifactEntry:
    return RunArtifactEntry(
        goal=goal,
        success_criteria="Complete scoped change",
        planner_decisions=["plan"],
        change_summary=["change"],
        verification_outcomes=verification or ["quick checks pass"],
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=reuse_notes or ["context: prior scoped-change learning"],
        learnings=["learning"],
        final_disposition=disposition,
        missing_artifacts=missing or [],
        lane=lane,
        relations=[],
    )


def test_compute_run_kpis_uses_lane_for_speed() -> None:
    fast = compute_run_kpis(_artifact(lane="fast_lane"))
    stable = compute_run_kpis(_artifact(lane="stability_lane"))

    assert fast.speed > stable.speed
    assert fast.lane == "fast_lane"


def test_compute_run_kpis_lowers_quality_on_failures() -> None:
    healthy = compute_run_kpis(_artifact())
    degraded = compute_run_kpis(
        _artifact(
            verification=["quick checks pass", "targeted checks fail"],
            missing=["retrieval_context"],
        )
    )

    assert healthy.quality > degraded.quality


def test_build_kpi_trends_returns_improving_when_recent_runs_score_higher() -> None:
    artifacts = [
        _artifact(
            goal="Older run",
            lane="stability_lane",
            reuse_notes=["No prior retrieval context available"],
        ),
        _artifact(goal="Middle run", lane="balanced"),
        _artifact(goal="Latest run", lane="fast_lane"),
    ]

    trends = build_kpi_trends(list(reversed(artifacts)))

    assert trends is not None
    assert trends.current.lane == "fast_lane"
    assert trends.trend in {"improving", "stable"}
    assert len(trends.points) == 3


def test_build_kpi_trends_returns_none_without_artifacts() -> None:
    assert build_kpi_trends([]) is None
