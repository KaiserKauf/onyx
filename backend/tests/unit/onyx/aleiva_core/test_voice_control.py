from pathlib import Path

from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.aleiva_core.second_brain.store import SecondBrainStore
from onyx.aleiva_core.voice_control import handle_voice_control
from onyx.aleiva_core.voice_control import VoiceControlRequest


def test_voice_control_start_run_enqueues_task(tmp_path: Path) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    response = handle_voice_control(
        VoiceControlRequest(intent="start-run", goal="Refactor parser"),
        queue=queue,
        second_brain_store=store,
    )

    assert response.status == "accepted"
    assert response.enqueued_task_id is not None
    assert response.queue["queued"] >= 1


def test_voice_control_pause_run_requires_task_id(tmp_path: Path) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    response = handle_voice_control(
        VoiceControlRequest(intent="pause-run"),
        queue=queue,
        second_brain_store=store,
    )

    assert response.status == "rejected"
    assert "task_id required" in response.message


def test_voice_control_report_is_read_only(tmp_path: Path) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    store = SecondBrainStore(tmp_path / "brain.jsonl")
    store.append_learning("backend:parser", "Prefer helper extraction", confidence=0.8)

    response = handle_voice_control(
        VoiceControlRequest(intent="report"),
        queue=queue,
        second_brain_store=store,
    )

    assert response.status == "accepted"
    assert response.report is not None
    assert "memory_hygiene_actions" in response.report
