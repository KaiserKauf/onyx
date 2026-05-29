from __future__ import annotations

import time
from dataclasses import dataclass

from onyx.aleiva_core.second_brain.store import LearningEntry


@dataclass(frozen=True)
class MemoryHygieneAction:
    action_type: str
    message: str
    topic: str
    learning: str
    contradicted_learning: str | None = None
    previous_confidence: float | None = None
    updated_confidence: float | None = None


@dataclass(frozen=True)
class ContradictionDecayResult:
    entries: list[LearningEntry]
    actions: list[MemoryHygieneAction]


def apply_contradiction_decay(
    entries: list[LearningEntry],
    *,
    decay_window_days: float = 30.0,
    min_decay_multiplier: float = 0.5,
    now_timestamp: float | None = None,
) -> ContradictionDecayResult:
    if decay_window_days <= 0:
        raise ValueError("decay_window_days must be greater than 0")
    if min_decay_multiplier <= 0 or min_decay_multiplier > 1:
        raise ValueError("min_decay_multiplier must be in (0, 1]")

    now = now_timestamp if now_timestamp is not None else time.time()
    decayed_entries: list[LearningEntry] = []
    actions: list[MemoryHygieneAction] = []

    for entry in entries:
        age_seconds = max(0.0, now - entry.created_at)
        age_days = age_seconds / 86400.0
        freshness_multiplier = max(
            min_decay_multiplier,
            1.0 - (age_days / decay_window_days),
        )
        decayed_confidence = round(entry.confidence * freshness_multiplier, 6)
        if decayed_confidence < entry.confidence:
            actions.append(
                MemoryHygieneAction(
                    action_type="decay",
                    message=(
                        "decayed stale memory "
                        f"'{entry.learning}' from {entry.confidence:.3f} "
                        f"to {decayed_confidence:.3f}"
                    ),
                    topic=entry.topic,
                    learning=entry.learning,
                    previous_confidence=entry.confidence,
                    updated_confidence=decayed_confidence,
                )
            )
        decayed_entries.append(
            LearningEntry(
                topic=entry.topic,
                learning=entry.learning,
                confidence=decayed_confidence,
                created_at=entry.created_at,
                contradicts=entry.contradicts,
            )
        )

    score_by_key: dict[tuple[str, str], float] = {}
    for entry in decayed_entries:
        key = (entry.topic, entry.learning)
        score_by_key[key] = max(
            score_by_key.get(key, 0.0),
            entry.confidence,
        )

    sample_entry_by_key: dict[tuple[str, str], LearningEntry] = {}
    for entry in decayed_entries:
        key = (entry.topic, entry.learning)
        existing = sample_entry_by_key.get(key)
        if existing is None or entry.confidence >= existing.confidence:
            sample_entry_by_key[key] = entry

    blocked_keys: set[tuple[str, str]] = set()
    seen_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
    for entry in decayed_entries:
        entry_key = (entry.topic, entry.learning)
        if not entry.contradicts:
            continue
        contradicted_key = (entry.topic, entry.contradicts)
        if contradicted_key not in score_by_key:
            continue
        pair = tuple(sorted((entry_key, contradicted_key)))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        current_score = score_by_key[entry_key]
        contradicted_score = score_by_key[contradicted_key]
        if current_score > contradicted_score:
            blocked_keys.add(contradicted_key)
            actions.append(
                MemoryHygieneAction(
                    action_type="contradiction",
                    message=(
                        f"tagged contradiction: '{entry.learning}' "
                        f"supersedes '{entry.contradicts}'"
                    ),
                    topic=entry.topic,
                    learning=entry.learning,
                    contradicted_learning=entry.contradicts,
                )
            )
        elif contradicted_score > current_score:
            blocked_keys.add(entry_key)
            actions.append(
                MemoryHygieneAction(
                    action_type="contradiction",
                    message=(
                        f"tagged contradiction: '{entry.contradicts}' "
                        f"remains over '{entry.learning}'"
                    ),
                    topic=entry.topic,
                    learning=entry.contradicts,
                    contradicted_learning=entry.learning,
                )
            )
        else:
            winner_key = min(entry_key, contradicted_key)
            loser_key = contradicted_key if winner_key == entry_key else entry_key
            blocked_keys.add(loser_key)
            winner_entry = sample_entry_by_key[winner_key]
            loser_entry = sample_entry_by_key[loser_key]
            actions.append(
                MemoryHygieneAction(
                    action_type="contradiction_tie_break",
                    message=(
                        "tagged contradiction tie-break: "
                        f"'{winner_entry.learning}' retained over "
                        f"'{loser_entry.learning}'"
                    ),
                    topic=winner_entry.topic,
                    learning=winner_entry.learning,
                    contradicted_learning=loser_entry.learning,
                )
            )

    filtered_entries = [
        entry
        for entry in decayed_entries
        if (entry.topic, entry.learning) not in blocked_keys
    ]
    if not actions:
        actions.append(
            MemoryHygieneAction(
                action_type="noop",
                message="no memory hygiene actions required",
                topic="",
                learning="",
            )
        )
    return ContradictionDecayResult(entries=filtered_entries, actions=actions)
