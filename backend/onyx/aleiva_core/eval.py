from __future__ import annotations

from typing import Literal

Lane = Literal["balanced", "fast_lane", "stability_lane"]


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


def _quality_drifted(
    current_quality: float,
    previous_quality: float | None,
    quality_drift_threshold: float,
) -> bool:
    if previous_quality is None:
        return False
    return previous_quality - current_quality >= quality_drift_threshold
