import pytest

from onyx.aleiva_core.second_brain.contradiction_decay import apply_contradiction_decay
from onyx.aleiva_core.second_brain.store import LearningEntry


def test_contradiction_decay_decays_and_tags_conflicts() -> None:
    now_timestamp = 120.0 * 86400.0
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="Use helper extraction",
            confidence=0.9,
            created_at=now_timestamp - (5.0 * 86400.0),
            contradicts=None,
        ),
        LearningEntry(
            topic="backend:parser",
            learning="Inline parsing logic",
            confidence=0.6,
            created_at=now_timestamp - (40.0 * 86400.0),
            contradicts="Use helper extraction",
        ),
    ]

    result = apply_contradiction_decay(entries, now_timestamp=now_timestamp)
    retained = [entry.learning for entry in result.entries]
    action_types = {action.action_type for action in result.actions}

    assert "Use helper extraction" in retained
    assert "Inline parsing logic" not in retained
    assert "decay" in action_types
    assert "contradiction" in action_types


def test_contradiction_decay_reports_noop_when_nothing_changes() -> None:
    now_timestamp = 86400.0
    entries = [
        LearningEntry(
            topic="backend:parser",
            learning="Prefer helper extraction",
            confidence=0.8,
            created_at=now_timestamp,
            contradicts=None,
        )
    ]

    result = apply_contradiction_decay(entries, now_timestamp=now_timestamp)

    assert len(result.entries) == 1
    assert result.entries[0].confidence == pytest.approx(0.8)
    assert [action.action_type for action in result.actions] == ["noop"]


def test_contradiction_decay_rejects_invalid_decay_configuration() -> None:
    with pytest.raises(ValueError, match="decay_window_days must be greater than 0"):
        apply_contradiction_decay([], decay_window_days=0)

    with pytest.raises(ValueError, match="min_decay_multiplier must be in \\(0, 1\\]"):
        apply_contradiction_decay([], min_decay_multiplier=0.0)
