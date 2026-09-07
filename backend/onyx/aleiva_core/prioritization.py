from __future__ import annotations

from dataclasses import dataclass

from onyx.aleiva_core.roi_priority import rank_tasks_by_roi
from onyx.aleiva_core.roi_priority import RoiTaskCandidate


@dataclass(frozen=True)
class PriorityCandidate:
    task: str
    impact: float
    confidence: float
    effort: float


@dataclass(frozen=True)
class PriorityScore:
    task: str
    score: float


def calculate_roi_priority(candidate: PriorityCandidate) -> PriorityScore:
    scored = rank_tasks_by_roi(
        [
            RoiTaskCandidate(
                task=candidate.task,
                impact=candidate.impact,
                confidence=candidate.confidence,
                effort=candidate.effort,
            )
        ]
    )[0]
    return PriorityScore(task=scored.task, score=scored.score)


def prioritize_tasks(candidates: list[PriorityCandidate]) -> list[PriorityScore]:
    scored = rank_tasks_by_roi(
        [
            RoiTaskCandidate(
                task=candidate.task,
                impact=candidate.impact,
                confidence=candidate.confidence,
                effort=candidate.effort,
            )
            for candidate in candidates
        ]
    )
    return [PriorityScore(task=entry.task, score=entry.score) for entry in scored]
