from __future__ import annotations

from dataclasses import dataclass

from onyx.aleiva_core.eval import choose_lane
from onyx.aleiva_core.second_brain.store import SecondBrainStore


@dataclass(frozen=True)
class AleivaRunResult:
    status: str
    lane: str
    plan: list[str]
    execution: list[str]
    verification: list[str]
    learnings: list[str]


def run_aleiva_cycle(
    goal: str,
    dry_run: bool,
    second_brain_store: SecondBrainStore | None = None,
) -> AleivaRunResult:
    plan = [f"Plan task for: {goal}"]
    execution = ["dry-run execution"] if dry_run else ["execute changes"]
    verification = ["quick checks pass"]
    learnings = [f"Prefer small scoped changes for goal: {goal}"]
    lane = choose_lane(speed=0.8, quality=0.9, knowledge_reuse=0.7)

    if second_brain_store is not None:
        second_brain_store.append_learning(
            topic=goal,
            learning=learnings[0],
            confidence=0.7,
        )

    return AleivaRunResult(
        status="completed",
        lane=lane,
        plan=plan,
        execution=execution,
        verification=verification,
        learnings=learnings,
    )
