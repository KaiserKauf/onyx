from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from onyx.aleiva_core.orchestrator import AleivaRunResult
from onyx.aleiva_core.orchestrator import run_aleiva_cycle
from onyx.aleiva_core.policy import PolicyTier
from onyx.aleiva_core.prioritization import calculate_roi_priority
from onyx.aleiva_core.prioritization import PriorityCandidate
from onyx.aleiva_core.second_brain.store import SecondBrainStore

TaskStatus = Literal["queued", "running", "completed", "failed", "paused"]


@dataclass(frozen=True)
class QueuedTask:
    task_id: str
    goal: str
    impact: float
    confidence: float
    effort: float
    priority_score: float
    status: TaskStatus
    tier: str
    created_at: float
    updated_at: float
    last_error: str | None = None


@dataclass(frozen=True)
class ControllerCycleResult:
    task: QueuedTask
    run_result: AleivaRunResult | None
    status: str
    reason: str


class AleivaTaskQueue:
    def __init__(self, path: Path, create_if_missing: bool = True) -> None:
        self.path = path
        if create_if_missing:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self._write_all([])

    def enqueue(
        self,
        goal: str,
        *,
        impact: float = 0.8,
        confidence: float = 0.85,
        effort: float = 1.0,
        tier: str = "normal",
    ) -> QueuedTask:
        now = time.time()
        score = calculate_roi_priority(
            PriorityCandidate(
                task=goal,
                impact=impact,
                confidence=confidence,
                effort=effort,
            )
        ).score
        task = QueuedTask(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            goal=goal.strip(),
            impact=impact,
            confidence=confidence,
            effort=effort,
            priority_score=score,
            status="queued",
            tier=tier,
            created_at=now,
            updated_at=now,
        )
        all_tasks = self._load_all()
        all_tasks.append(task)
        self._write_all(all_tasks)
        return task

    def list_tasks(self, *, status: TaskStatus | None = None, limit: int = 100) -> list[QueuedTask]:
        if limit <= 0:
            return []
        all_tasks = self._load_all()
        if status is not None:
            all_tasks = [task for task in all_tasks if task.status == status]
        sorted_tasks = sorted(
            all_tasks,
            key=lambda task: (task.priority_score, -task.created_at),
            reverse=True,
        )
        return sorted_tasks[:limit]

    def pop_next(self) -> QueuedTask | None:
        all_tasks = self._load_all()
        queued_tasks = [task for task in all_tasks if task.status == "queued"]
        if not queued_tasks:
            return None

        selected = sorted(
            queued_tasks,
            key=lambda task: (task.priority_score, -task.created_at),
            reverse=True,
        )[0]
        return self._update_status(selected.task_id, status="running")

    def mark_completed(self, task_id: str) -> QueuedTask | None:
        return self._update_status(task_id, status="completed")

    def mark_paused(self, task_id: str) -> QueuedTask | None:
        return self._update_status(task_id, status="paused")

    def mark_failed(self, task_id: str, *, error: str) -> QueuedTask | None:
        return self._update_status(task_id, status="failed", last_error=error)

    def _update_status(
        self,
        task_id: str,
        *,
        status: TaskStatus,
        last_error: str | None = None,
    ) -> QueuedTask | None:
        now = time.time()
        all_tasks = self._load_all()
        updated_task: QueuedTask | None = None
        rewritten: list[QueuedTask] = []
        for task in all_tasks:
            if task.task_id != task_id:
                rewritten.append(task)
                continue
            updated_task = QueuedTask(
                task_id=task.task_id,
                goal=task.goal,
                impact=task.impact,
                confidence=task.confidence,
                effort=task.effort,
                priority_score=task.priority_score,
                status=status,
                tier=task.tier,
                created_at=task.created_at,
                updated_at=now,
                last_error=last_error,
            )
            rewritten.append(updated_task)
        if updated_task is None:
            return None
        self._write_all(rewritten)
        return updated_task

    def _load_all(self) -> list[QueuedTask]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []

        loaded: list[QueuedTask] = []
        for row in payload:
            if not isinstance(row, dict):
                continue
            try:
                loaded.append(
                    QueuedTask(
                        task_id=str(row["task_id"]),
                        goal=str(row["goal"]),
                        impact=float(row["impact"]),
                        confidence=float(row["confidence"]),
                        effort=float(row["effort"]),
                        priority_score=float(row["priority_score"]),
                        status=str(row["status"]),  # type: ignore[arg-type]
                        tier=str(row.get("tier", "normal")),
                        created_at=float(row["created_at"]),
                        updated_at=float(row["updated_at"]),
                        last_error=(
                            str(row["last_error"])
                            if row.get("last_error") is not None
                            else None
                        ),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return loaded

    def _write_all(self, tasks: list[QueuedTask]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(task) for task in tasks]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


class AleivaAutopilotController:
    def __init__(
        self,
        queue: AleivaTaskQueue,
        *,
        max_iterations_per_run: int = 20,
    ) -> None:
        self.queue = queue
        self.max_iterations_per_run = max_iterations_per_run

    def run_until_idle(
        self,
        *,
        dry_run: bool,
        second_brain_store: SecondBrainStore | None,
    ) -> list[ControllerCycleResult]:
        outcomes: list[ControllerCycleResult] = []
        for _ in range(self.max_iterations_per_run):
            current = self.queue.pop_next()
            if current is None:
                break

            try:
                run_result = run_aleiva_cycle(
                    goal=current.goal,
                    dry_run=dry_run,
                    policy_tier=_coerce_policy_tier(current.tier),
                    second_brain_store=second_brain_store,
                )
            except (OSError, ValueError, TypeError) as exc:
                failed = self.queue.mark_failed(current.task_id, error=str(exc))
                outcomes.append(
                    ControllerCycleResult(
                        task=failed or current,
                        run_result=None,
                        status="failed",
                        reason="execution_error",
                    )
                )
                continue

            final_task = (
                self.queue.mark_completed(current.task_id)
                if run_result.status == "completed"
                else self.queue.mark_failed(
                    current.task_id,
                    error="run_incomplete_missing_artifacts",
                )
            )
            outcomes.append(
                ControllerCycleResult(
                    task=final_task or current,
                    run_result=run_result,
                    status=run_result.status,
                    reason=(
                        "completed"
                        if run_result.status == "completed"
                        else "incomplete_missing_artifacts"
                    ),
                )
            )

        return outcomes


def _coerce_policy_tier(tier: str) -> PolicyTier:
    normalized_tier = tier.strip().lower()
    if normalized_tier in {"safe", "normal", "experimental"}:
        return normalized_tier  # type: ignore[return-value]
    return "normal"
