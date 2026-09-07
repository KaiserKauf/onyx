from __future__ import annotations

from dataclasses import dataclass

from onyx.aleiva_core.second_brain.contradiction_decay import apply_contradiction_decay
from onyx.aleiva_core.second_brain.contradiction_decay import MemoryHygieneAction
from onyx.aleiva_core.second_brain.store import LearningEntry


@dataclass(frozen=True)
class MemoryHygieneResult:
    entries: list[LearningEntry]
    actions: list[str]
    action_details: list[MemoryHygieneAction]


@dataclass(frozen=True)
class ScheduledHygieneSummary:
    entries: list[LearningEntry]
    deduplicated_count: int
    decay_action_count: int
    contradiction_guidance: list[str]
    actions: list[str]


def apply_memory_hygiene(
    entries: list[LearningEntry],
    *,
    decay_window_days: float = 30.0,
    min_decay_multiplier: float = 0.5,
    now_timestamp: float | None = None,
) -> MemoryHygieneResult:
    contradiction_decay_result = apply_contradiction_decay(
        entries,
        decay_window_days=decay_window_days,
        min_decay_multiplier=min_decay_multiplier,
        now_timestamp=now_timestamp,
    )
    return MemoryHygieneResult(
        entries=contradiction_decay_result.entries,
        actions=[entry.message for entry in contradiction_decay_result.actions],
        action_details=contradiction_decay_result.actions,
    )


def run_scheduled_hygiene(
    entries: list[LearningEntry],
    *,
    decay_window_days: float = 30.0,
    min_decay_multiplier: float = 0.5,
    now_timestamp: float | None = None,
) -> ScheduledHygieneSummary:
    deduped_entries = _deduplicate_entries(entries)
    hygiene_result = apply_memory_hygiene(
        deduped_entries,
        decay_window_days=decay_window_days,
        min_decay_multiplier=min_decay_multiplier,
        now_timestamp=now_timestamp,
    )
    contradiction_guidance = [
        detail.message
        for detail in hygiene_result.action_details
        if detail.action_type.startswith("contradiction")
    ]
    decay_action_count = sum(
        1 for detail in hygiene_result.action_details if detail.action_type == "decay"
    )
    return ScheduledHygieneSummary(
        entries=hygiene_result.entries,
        deduplicated_count=max(0, len(entries) - len(deduped_entries)),
        decay_action_count=decay_action_count,
        contradiction_guidance=contradiction_guidance,
        actions=hygiene_result.actions,
    )


def _deduplicate_entries(entries: list[LearningEntry]) -> list[LearningEntry]:
    deduped_by_key: dict[tuple[str, str], LearningEntry] = {}
    for entry in entries:
        key = (entry.topic, entry.learning)
        current = deduped_by_key.get(key)
        if current is None:
            deduped_by_key[key] = entry
            continue
        if entry.confidence > current.confidence:
            deduped_by_key[key] = entry
            continue
        if entry.confidence == current.confidence and entry.created_at > current.created_at:
            deduped_by_key[key] = entry
    return list(deduped_by_key.values())
