from pathlib import Path

from onyx.aleiva_core.eval import choose_lane
from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.aleiva_core.second_brain.store import SecondBrainStore


def test_choose_lane_moves_to_stability_when_quality_drops() -> None:
    lane = choose_lane(speed=0.8, quality=0.3, knowledge_reuse=0.7)
    assert lane == "stability_lane"


def test_choose_lane_moves_to_fast_lane_when_all_kpis_are_high() -> None:
    lane = choose_lane(speed=0.9, quality=0.9, knowledge_reuse=0.8)
    assert lane == "fast_lane"


def test_run_cycle_records_learning(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    result = run_aleiva_cycle(
        goal="Refactor parser",
        dry_run=True,
        second_brain_store=store,
    )

    assert result.status == "completed"
    assert len(result.learnings) > 0

    persisted = store.retrieve("Refactor parser", limit=5)
    assert len(persisted) == 1
    assert "Prefer small scoped changes" in persisted[0].learning
