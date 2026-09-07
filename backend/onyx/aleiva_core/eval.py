from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from onyx.aleiva_core.second_brain.store import RunArtifactEntry

Lane = Literal["balanced", "fast_lane", "stability_lane"]
TrendDirection = Literal["improving", "stable", "declining"]

_LANE_SPEED: dict[str, float] = {
    "fast_lane": 0.9,
    "balanced": 0.75,
    "stability_lane": 0.55,
}


@dataclass(frozen=True)
class AleivaKpiSnapshot:
    speed: float
    quality: float
    knowledge_reuse: float
    lane: str


@dataclass(frozen=True)
class AleivaKpiTrendPoint:
    run_index: int
    goal: str
    speed: float
    quality: float
    knowledge_reuse: float
    lane: str


@dataclass(frozen=True)
class AleivaKpiTrends:
    current: AleivaKpiSnapshot
    trend: TrendDirection
    points: list[AleivaKpiTrendPoint]


def choose_lane(
    speed: float,
    quality: float,
    knowledge_reuse: float,
    previous_quality: float | None = None,
    quality_drift_threshold: float = 0.15,
) -> Lane:
    if _quality_drifted(
        current_quality=quality,
        previous_quality=previous_quality,
        quality_drift_threshold=quality_drift_threshold,
    ):
        return "stability_lane"
    if quality < 0.6:
        return "stability_lane"
    if speed > 0.8 and quality > 0.8 and knowledge_reuse > 0.6:
        return "fast_lane"
    return "balanced"


def compute_run_kpis(artifact: RunArtifactEntry) -> AleivaKpiSnapshot:
    lane = artifact.lane if artifact.lane in _LANE_SPEED else "balanced"
    speed = _LANE_SPEED.get(lane, 0.75)

    quality = 0.9 if artifact.final_disposition == "completed" else 0.45
    if any("fail" in outcome.lower() for outcome in artifact.verification_outcomes):
        quality = max(0.2, quality - 0.25)
    if artifact.missing_artifacts:
        quality = max(0.2, quality - 0.15)

    context_notes = [
        note
        for note in artifact.reuse_notes
        if note.startswith("context:") or "prior learning" in note.lower()
    ]
    knowledge_reuse = min(1.0, 0.35 + 0.15 * len(context_notes))
    if any("No prior retrieval" in note for note in artifact.reuse_notes):
        knowledge_reuse = min(knowledge_reuse, 0.4)

    return AleivaKpiSnapshot(
        speed=round(speed, 3),
        quality=round(quality, 3),
        knowledge_reuse=round(knowledge_reuse, 3),
        lane=lane,
    )


def build_kpi_trends(artifacts: list[RunArtifactEntry]) -> AleivaKpiTrends | None:
    if not artifacts:
        return None

    chronological = list(reversed(artifacts))
    points: list[AleivaKpiTrendPoint] = []
    for index, artifact in enumerate(chronological):
        snapshot = compute_run_kpis(artifact)
        points.append(
            AleivaKpiTrendPoint(
                run_index=index + 1,
                goal=artifact.goal,
                speed=snapshot.speed,
                quality=snapshot.quality,
                knowledge_reuse=snapshot.knowledge_reuse,
                lane=snapshot.lane,
            )
        )

    current = compute_run_kpis(artifacts[0])
    trend = _compute_trend_direction(points)

    return AleivaKpiTrends(current=current, trend=trend, points=points[-10:])


def _quality_drifted(
    current_quality: float,
    previous_quality: float | None,
    quality_drift_threshold: float,
) -> bool:
    if previous_quality is None:
        return False
    return previous_quality - current_quality >= quality_drift_threshold


def _compute_trend_direction(points: list[AleivaKpiTrendPoint]) -> TrendDirection:
    if len(points) < 2:
        return "stable"

    recent = points[-3:]
    older = points[-6:-3] if len(points) >= 6 else points[: max(1, len(points) - len(recent))]
    if not older:
        return "stable"

    def composite(point: AleivaKpiTrendPoint) -> float:
        return (point.speed + point.quality + point.knowledge_reuse) / 3

    recent_avg = sum(composite(point) for point in recent) / len(recent)
    older_avg = sum(composite(point) for point in older) / len(older)
    delta = recent_avg - older_avg

    if delta >= 0.05:
        return "improving"
    if delta <= -0.05:
        return "declining"
    return "stable"
