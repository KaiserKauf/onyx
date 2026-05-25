from __future__ import annotations

from typing import Literal

Lane = Literal["balanced", "fast_lane", "stability_lane"]


def choose_lane(speed: float, quality: float, knowledge_reuse: float) -> Lane:
    if quality < 0.6:
        return "stability_lane"
    if speed > 0.8 and quality > 0.8 and knowledge_reuse > 0.6:
        return "fast_lane"
    return "balanced"
