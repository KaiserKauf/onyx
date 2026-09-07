from pathlib import Path

from onyx.aleiva_core.controller import AleivaAutopilotController
from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.aleiva_core.second_brain.store import SecondBrainStore


def test_task_queue_prioritizes_higher_roi_task(tmp_path: Path) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    queue.enqueue(
        "low value",
        impact=0.5,
        confidence=0.6,
        effort=1.4,
    )
    high_priority = queue.enqueue(
        "high value",
        impact=0.95,
        confidence=0.9,
        effort=0.9,
    )

    popped = queue.pop_next()
    assert popped is not None
    assert popped.task_id == high_priority.task_id
    assert popped.status == "running"


def test_task_queue_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "queue.json"
    queue = AleivaTaskQueue(path)
    queued = queue.enqueue("persist me")

    reloaded_queue = AleivaTaskQueue(path, create_if_missing=False)
    listed = reloaded_queue.list_tasks(limit=10)
    assert len(listed) == 1
    assert listed[0].task_id == queued.task_id
    assert listed[0].goal == "persist me"


def test_autopilot_controller_executes_plan_execute_verify_learn_cycle(
    tmp_path: Path,
) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    queue.enqueue("Refactor parser")
    controller = AleivaAutopilotController(queue=queue, max_iterations_per_run=5)
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    results = controller.run_until_idle(dry_run=False, second_brain_store=store)

    assert len(results) == 1
    assert results[0].status == "completed"
    assert results[0].run_result is not None
    assert results[0].run_result.plan
    assert results[0].run_result.execution
    assert results[0].run_result.verification
    assert results[0].run_result.learnings
    assert queue.list_tasks(status="completed", limit=10)


def test_autopilot_controller_applies_queued_task_policy_tier(
    tmp_path: Path,
) -> None:
    queue = AleivaTaskQueue(tmp_path / "queue.json")
    queue.enqueue("Refactor parser", tier="safe")
    controller = AleivaAutopilotController(queue=queue, max_iterations_per_run=5)
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    results = controller.run_until_idle(dry_run=True, second_brain_store=store)

    assert len(results) == 1
    assert results[0].run_result is not None
    assert results[0].run_result.policy_tier == "safe"
    assert results[0].run_result.policy_controls is not None
    assert results[0].run_result.policy_controls["max_commands_per_run"] == 5
