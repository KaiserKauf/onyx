import pytest

from onyx.aleiva_core.second_brain.hygiene import apply_memory_hygiene
from onyx.aleiva_core.second_brain.hygiene import run_scheduled_hygiene
from onyx.aleiva_core.second_brain.store import LearningEntry


def test_memory_hygiene_decays_stale_entries() -> None:
    now_timestamp = 200.0 * 86400.0
    stale_entry = LearningEntry(
        topic="backend:parser",
        learning="Prefer helper extraction",
        confidence=0.8,
        created_at=now_timestamp - (120.0 * 86400.0),
        contradicts=None,
    )

    result = apply_memory_hygiene([stale_entry], now_timestamp=now_timestamp)

    assert len(result.entries) == 1
    assert result.entries[0].confidence == pytest.approx(0.4)
    assert any("decayed stale memory" in action for action in result.actions)
    assert any(action.action_type == "decay" for action in result.action_details)


def test_memory_hygiene_tags_contradictions_and_keeps_stronger_entry() -> None:
    now_timestamp = 100.0
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="Use helper extraction",
            confidence=0.9,
            created_at=now_timestamp,
            contradicts=None,
        ),
        LearningEntry(
            topic="backend:parser",
            learning="Inline parsing logic",
            confidence=0.6,
            created_at=now_timestamp,
            contradicts="Use helper extraction",
        ),
    ]

    result = apply_memory_hygiene(entries, now_timestamp=now_timestamp)
    learnings = [entry.learning for entry in result.entries]

    assert "Use helper extraction" in learnings
    assert "Inline parsing logic" not in learnings
    assert any("tagged contradiction" in action for action in result.actions)
    assert any(action.action_type == "contradiction" for action in result.action_details)


def test_memory_hygiene_rejects_invalid_decay_configuration() -> None:
    with pytest.raises(ValueError, match="decay_window_days must be greater than 0"):
        apply_memory_hygiene([], decay_window_days=0)

    with pytest.raises(ValueError, match="min_decay_multiplier must be in \\(0, 1\\]"):
        apply_memory_hygiene([], min_decay_multiplier=0.0)


def test_memory_hygiene_reports_noop_action_when_no_changes_are_needed() -> None:
    now_timestamp = 86400.0
    fresh_entry = LearningEntry(
        topic="backend:parser",
        learning="Prefer helper extraction",
        confidence=0.8,
        created_at=now_timestamp,
        contradicts=None,
    )

    result = apply_memory_hygiene(
        [fresh_entry],
        now_timestamp=now_timestamp,
    )

    assert len(result.entries) == 1
    assert result.entries[0].confidence == pytest.approx(0.8)
    assert result.actions == ["no memory hygiene actions required"]
    assert [action.action_type for action in result.action_details] == ["noop"]


def test_memory_hygiene_does_not_block_same_learning_across_topics() -> None:
    now_timestamp = 100.0
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="Use helper extraction",
            confidence=0.8,
            created_at=now_timestamp,
            contradicts=None,
        ),
        LearningEntry(
            topic="backend:parser",
            learning="Inline parsing logic",
            confidence=0.7,
            created_at=now_timestamp,
            contradicts="Use helper extraction",
        ),
        LearningEntry(
            topic="frontend:parser",
            learning="Use helper extraction",
            confidence=0.75,
            created_at=now_timestamp,
            contradicts=None,
        ),
    ]

    result = apply_memory_hygiene(entries, now_timestamp=now_timestamp)
    retained = {(entry.topic, entry.learning) for entry in result.entries}
    assert ("frontend:parser", "Use helper extraction") in retained


def test_memory_hygiene_tie_break_keeps_single_contradiction_winner() -> None:
    now_timestamp = 100.0
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="A",
            confidence=0.8,
            created_at=now_timestamp,
            contradicts="B",
        ),
        LearningEntry(
            topic="backend:parser",
            learning="B",
            confidence=0.8,
            created_at=now_timestamp,
            contradicts="A",
        ),
    ]

    result = apply_memory_hygiene(entries, now_timestamp=now_timestamp)
    retained = [entry.learning for entry in result.entries]
    assert len(retained) == 1
    assert any("tie-break" in action for action in result.actions)


def test_scheduled_hygiene_reports_dedup_and_contradiction_guidance() -> None:
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="Use helper extraction",
            confidence=0.5,
            created_at=1.0,
            contradicts=None,
        ),
        LearningEntry(
            topic="backend:parser",
            learning="Use helper extraction",
            confidence=0.8,
            created_at=2.0,
            contradicts=None,
        ),
        LearningEntry(
            topic="backend:parser",
            learning="Inline parser",
            confidence=0.6,
            created_at=2.0,
            contradicts="Use helper extraction",
        ),
    ]
    summary = run_scheduled_hygiene(entries, now_timestamp=2.0)

    assert summary.deduplicated_count == 1
    assert summary.actions
    assert summary.contradiction_guidance
