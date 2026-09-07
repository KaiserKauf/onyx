from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from onyx.aleiva_core.controller import AleivaTaskQueue
from onyx.aleiva_core.second_brain.hygiene import apply_memory_hygiene
from onyx.aleiva_core.second_brain.store import SecondBrainStore

VoiceIntent = Literal["start-run", "pause-run", "status", "report"]


@dataclass(frozen=True)
class VoiceControlRequest:
    intent: VoiceIntent
    goal: str | None = None
    task_id: str | None = None
    policy_tier: str = "safe"


@dataclass(frozen=True)
class VoiceControlResponse:
    status: str
    message: str
    queue: dict[str, int]
    enqueued_task_id: str | None = None
    report: dict[str, object] | None = None


def handle_voice_control(
    request: VoiceControlRequest,
    *,
    queue: AleivaTaskQueue,
    second_brain_store: SecondBrainStore,
) -> VoiceControlResponse:
    if request.intent == "start-run":
        goal = (request.goal or "").strip()
        if not goal:
            return VoiceControlResponse(
                status="rejected",
                message="goal required for start-run",
                queue=_queue_summary(queue),
            )
        queued = queue.enqueue(goal=goal, tier=request.policy_tier)
        return VoiceControlResponse(
            status="accepted",
            message="queued autonomous run request",
            enqueued_task_id=queued.task_id,
            queue=_queue_summary(queue),
        )

    if request.intent == "pause-run":
        task_id = (request.task_id or "").strip()
        if not task_id:
            return VoiceControlResponse(
                status="rejected",
                message="task_id required for pause-run",
                queue=_queue_summary(queue),
            )
        paused = queue.mark_paused(task_id)
        if paused is None:
            return VoiceControlResponse(
                status="rejected",
                message="task not found",
                queue=_queue_summary(queue),
            )
        return VoiceControlResponse(
            status="accepted",
            message="task paused",
            queue=_queue_summary(queue),
        )

    if request.intent == "status":
        return VoiceControlResponse(
            status="accepted",
            message="current run queue status",
            queue=_queue_summary(queue),
        )

    # "report" stays read-only and never triggers command execution.
    run_artifacts = second_brain_store.list_run_artifacts(limit=5)
    sampled_entries = second_brain_store.list_learnings(limit=20)
    hygiene = apply_memory_hygiene(sampled_entries)
    return VoiceControlResponse(
        status="accepted",
        message="control-plane report generated",
        queue=_queue_summary(queue),
        report={
            "recent_runs": [
                {
                    "goal": artifact.goal,
                    "final_disposition": artifact.final_disposition,
                    "missing_artifacts": artifact.missing_artifacts,
                }
                for artifact in run_artifacts
            ],
            "memory_hygiene_actions": hygiene.actions,
        },
    )


def _queue_summary(queue: AleivaTaskQueue) -> dict[str, int]:
    tasks = queue.list_tasks(limit=200)
    return {
        "queued": sum(1 for task in tasks if task.status == "queued"),
        "running": sum(1 for task in tasks if task.status == "running"),
        "completed": sum(1 for task in tasks if task.status == "completed"),
        "failed": sum(1 for task in tasks if task.status == "failed"),
        "paused": sum(1 for task in tasks if task.status == "paused"),
    }
