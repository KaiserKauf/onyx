from __future__ import annotations

from dataclasses import dataclass

from onyx.aleiva_core.codebase_snapshot import CodebaseSnapshot
from onyx.aleiva_core.codebase_snapshot import CodebaseSnapshotStore
from onyx.aleiva_core.platforms import list_platforms
from onyx.aleiva_core.second_brain.store import LearningEntry
from onyx.aleiva_core.second_brain.store import RunArtifactEntry
from onyx.aleiva_core.second_brain.store import SecondBrainStore


@dataclass(frozen=True)
class PlatformLearningSummary:
    platform_id: str
    display_name: str
    learning_count: int
    latest_learning: str | None
    run_count: int
    latest_run_disposition: str | None
    latest_snapshot_commit: str | None
    latest_snapshot_dirty: bool | None


@dataclass(frozen=True)
class AgentLearningStatus:
    total_learnings: int
    total_runs: int
    dry_run_persistence: str
    platforms: list[PlatformLearningSummary]
    latest_snapshots: list[CodebaseSnapshot]


def build_agent_learning_status(
    store: SecondBrainStore,
    snapshot_store: CodebaseSnapshotStore,
) -> AgentLearningStatus:
    all_learnings = store.list_learnings(limit=500)
    all_runs = store.list_run_artifacts(limit=200)
    snapshots = snapshot_store.list_snapshots(limit=10)
    platform_summaries = [
        _summarize_platform(platform.id, platform.display_name, all_learnings, all_runs, snapshots)
        for platform in list_platforms()
    ]
    return AgentLearningStatus(
        total_learnings=len(all_learnings),
        total_runs=len(all_runs),
        dry_run_persistence="disabled_by_design",
        platforms=platform_summaries,
        latest_snapshots=snapshots,
    )


def _summarize_platform(
    platform_id: str,
    display_name: str,
    learnings: list[LearningEntry],
    runs: list[RunArtifactEntry],
    snapshots: list[CodebaseSnapshot],
) -> PlatformLearningSummary:
    prefix = f"{platform_id}:"
    platform_learnings = [
        entry for entry in learnings if entry.topic.lower().startswith(prefix)
    ]
    platform_runs = [
        run for run in runs if run.goal.lower().startswith(prefix)
    ]
    platform_snapshots = [
        snapshot
        for snapshot in snapshots
        if snapshot.platform_id == platform_id
    ]
    latest_learning = platform_learnings[-1].learning if platform_learnings else None
    latest_run = platform_runs[0] if platform_runs else None
    latest_snapshot = platform_snapshots[0] if platform_snapshots else None
    return PlatformLearningSummary(
        platform_id=platform_id,
        display_name=display_name,
        learning_count=len(platform_learnings),
        latest_learning=latest_learning,
        run_count=len(platform_runs),
        latest_run_disposition=latest_run.final_disposition if latest_run else None,
        latest_snapshot_commit=latest_snapshot.head_commit if latest_snapshot else None,
        latest_snapshot_dirty=latest_snapshot.is_dirty if latest_snapshot else None,
    )
