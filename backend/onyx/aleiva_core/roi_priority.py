from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoiTaskCandidate:
    task: str
    impact: float
    confidence: float
    effort: float


@dataclass(frozen=True)
class RoiPriorityScore:
    task: str
    impact: float
    confidence: float
    effort: float
    score: float


def score_roi_task(candidate: RoiTaskCandidate) -> RoiPriorityScore:
    if candidate.effort <= 0:
        raise ValueError("effort must be greater than 0")

    score = (candidate.impact * candidate.confidence) / candidate.effort
    return RoiPriorityScore(
        task=candidate.task,
        impact=candidate.impact,
        confidence=candidate.confidence,
        effort=candidate.effort,
        score=score,
    )


def rank_tasks_by_roi(candidates: list[RoiTaskCandidate]) -> list[RoiPriorityScore]:
    scored = [score_roi_task(candidate) for candidate in candidates]
    return sorted(scored, key=lambda entry: entry.score, reverse=True)
