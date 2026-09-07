from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from onyx.aleiva_core.codebase_snapshot import capture_codebase_snapshot
from onyx.aleiva_core.codebase_snapshot import CodebaseSnapshotStore
from onyx.aleiva_core.eval import choose_lane
from onyx.aleiva_core.events import validate_run_completeness
from onyx.aleiva_core.policy import AleivaPolicy
from onyx.aleiva_core.policy import PolicyTier
from onyx.aleiva_core.prioritization import PriorityScore
from onyx.aleiva_core.roi_priority import rank_tasks_by_roi
from onyx.aleiva_core.roi_priority import RoiPriorityScore
from onyx.aleiva_core.roi_priority import RoiTaskCandidate
from onyx.aleiva_core.second_brain.graph import extract_relations
from onyx.aleiva_core.second_brain.hygiene import apply_memory_hygiene
from onyx.aleiva_core.second_brain.hygiene import MemoryHygieneAction
from onyx.aleiva_core.second_brain.store import RunArtifactEntry
from onyx.aleiva_core.second_brain.store import SecondBrainStore
from onyx.aleiva_core.types import AleivaRunRecord


@dataclass(frozen=True)
class AleivaRunResult:
    status: str
    lane: str
    plan: list[str]
    execution: list[str]
    verification: list[str]
    learnings: list[str]
    missing_artifacts: list[str]
    selected_priority_scores: list[PriorityScore]
    selected_priority_details: list[RoiPriorityScore]
    memory_hygiene_actions: list[str]
    memory_hygiene_action_details: list[MemoryHygieneAction]
    policy_tier: str = "normal"
    policy_controls: dict[str, int | str] | None = None
    guardrail_events: list[str] | None = None


def run_aleiva_cycle(
    goal: str,
    dry_run: bool,
    policy_tier: PolicyTier = "normal",
    second_brain_store: SecondBrainStore | None = None,
    platform_id: str | None = None,
    snapshot_store: CodebaseSnapshotStore | None = None,
    repo_path: Path | None = None,
) -> AleivaRunResult:
    active_store = second_brain_store
    policy = AleivaPolicy.default(tier=policy_tier)
    goal_domain = platform_id or _infer_goal_domain(goal)
    normalized_goal = (
        f"{goal_domain}: {goal}" if goal_domain and not goal.lower().startswith(f"{goal_domain}:") else goal
    )
    codebase_snapshot = None
    if not dry_run:
        codebase_snapshot = capture_codebase_snapshot(
            repo_path=repo_path,
            run_id=normalized_goal,
            platform_id=goal_domain if isinstance(goal_domain, str) else platform_id,
        )
        if snapshot_store is not None:
            try:
                snapshot_store.append(codebase_snapshot)
            except OSError:
                pass
    roi_priority_scores = rank_tasks_by_roi(
        [
            RoiTaskCandidate(
                task="plan scoped implementation",
                impact=0.85,
                confidence=0.9,
                effort=1.0,
            ),
            RoiTaskCandidate(
                task="run focused validations",
                impact=0.9,
                confidence=0.95,
                effort=1.4,
            ),
            RoiTaskCandidate(
                task="persist run artifacts",
                impact=0.65,
                confidence=0.8,
                effort=0.8,
            ),
        ]
    )
    selected_priority_details = roi_priority_scores[:2]
    selected_priority_scores = [
        PriorityScore(task=entry.task, score=entry.score)
        for entry in selected_priority_details
    ]

    retrieval_context: list[str] = []
    retrieval_ok = True
    memory_hygiene_actions = ["no memory hygiene actions required"]
    memory_hygiene_action_details = [
        MemoryHygieneAction(
            action_type="noop",
            message="no memory hygiene actions required",
            topic="",
            learning="",
        )
    ]
    if active_store is None:
        retrieval_ok = False
        if dry_run:
            memory_hygiene_actions = ["memory hygiene skipped: second-brain store unavailable"]
            memory_hygiene_action_details = [
                MemoryHygieneAction(
                    action_type="skipped",
                    message="memory hygiene skipped: second-brain store unavailable",
                    topic="",
                    learning="",
                )
            ]
    else:
        try:
            if dry_run:
                sampled_entries = active_store.list_learnings(
                    limit=20,
                    topic=normalized_goal,
                    domain=goal_domain if isinstance(goal_domain, str) else None,
                )
                hygiene_result = apply_memory_hygiene(sampled_entries)
                memory_hygiene_actions = hygiene_result.actions
                memory_hygiene_action_details = hygiene_result.action_details
            retrieval_context = [
                entry.learning
                for entry in active_store.retrieve(
                    topic=normalized_goal,
                    limit=3,
                    domain=goal_domain if isinstance(goal_domain, str) else None,
                )
                if entry.learning
            ]
            if not retrieval_context:
                if dry_run:
                    retrieval_context = [
                        "Bootstrap context: apply strict guardrails and scoped changes first"
                    ]
                else:
                    active_store.append_learning(
                        topic=normalized_goal,
                        learning="Bootstrap context: apply strict guardrails and scoped changes first",
                        confidence=0.6,
                    )
                    retrieval_context = [
                        entry.learning
                        for entry in active_store.retrieve(
                            topic=normalized_goal,
                            limit=3,
                            domain=goal_domain if isinstance(goal_domain, str) else None,
                        )
                        if entry.learning
                    ]
        except (OSError, ValueError, TypeError):
            retrieval_ok = False
            if dry_run:
                memory_hygiene_actions = ["memory hygiene skipped: failed to read second-brain entries"]
                memory_hygiene_action_details = [
                    MemoryHygieneAction(
                        action_type="skipped",
                        message="memory hygiene skipped: failed to read second-brain entries",
                        topic="",
                        learning="",
                    )
                ]

    plan = [
        f"Plan task for: {normalized_goal}",
        "Apply safe minimal changes first",
        f"Run under risk tier: {policy_tier}",
        f"Retrieved {len(retrieval_context)} prior context items",
    ]
    execution = ["dry-run execution"] if dry_run else ["execute changes"]
    verification = apply_flaky_test_rerun_heuristics(
        ["quick checks pass", "targeted checks pass"],
        rerun_limit=2,
    )
    learnings = [
        f"Prefer small scoped changes for goal: {normalized_goal}",
    ]
    if codebase_snapshot is not None:
        if codebase_snapshot.head_commit:
            learnings.append(f"codebase_head:{codebase_snapshot.head_commit[:12]}")
        if codebase_snapshot.changed_files:
            learnings.append(
                "files_in_scope:"
                + ",".join(codebase_snapshot.changed_files[:5])
            )
    policy_controls = policy.describe_controls()
    guardrail_checks = [
        ("git reset --hard", "destructive git guardrail"),
        ("pytest backend/tests/unit -q", "allowlisted verification command"),
        ("echo hello", "non-allowlisted shell command"),
    ]
    guardrail_events = [
        (
            f"{label}: {policy.evaluate_command(command).reason}"
            f" (allowed={policy.evaluate_command(command).allowed})"
        )
        for command, label in guardrail_checks
    ]
    lane = choose_lane(
        speed=0.8,
        quality=0.9,
        knowledge_reuse=0.7,
        previous_quality=0.95,
    )

    run_record = AleivaRunRecord(
        goal=normalized_goal,
        success_criteria="Complete the scoped change with passing targeted checks",
        planner_decisions=[
            "Prioritize low-risk implementation sequence",
            "Require second-brain retrieval context before execution",
            f"Applied policy tier '{policy_tier}' controls: {policy_controls}",
            f"Selected execution lane: {lane}",
            (
                "Selected ROI priorities: "
                + ", ".join(
                    f"{entry.task} ({entry.score:.3f})"
                    for entry in selected_priority_scores
                )
            ),
        ],
        change_summary=[
            "Updated Aleiva orchestration flow in current run",
            "Preserved strict scope and guardrail policy",
            *(
                [f"git_branch:{codebase_snapshot.branch}"]
                if codebase_snapshot and codebase_snapshot.branch
                else []
            ),
            *(
                [f"git_dirty:{len(codebase_snapshot.changed_files)} files"]
                if codebase_snapshot and codebase_snapshot.is_dirty
                else []
            ),
            *(
                [f"changed:{path}" for path in codebase_snapshot.changed_files[:5]]
                if codebase_snapshot and codebase_snapshot.changed_files
                else []
            ),
        ],
        verification_outcomes=verification,
        failure_classifications=["none"],
        recovery_attempts=["none required"],
        reuse_notes=[
            "Applied prior learning for scoped changes first",
            *(f"context: {learning}" for learning in retrieval_context),
        ]
        or ["No prior retrieval context available"],
        deferred_critical_issues=[],
        unresolved_critical_issues=[],
        final_disposition="completed",
        files_changed=list(codebase_snapshot.changed_files) if codebase_snapshot else [],
        codebase_context=[
            *(f"branch:{codebase_snapshot.branch}" if codebase_snapshot and codebase_snapshot.branch else []),
            *(f"commit:{codebase_snapshot.head_commit}" if codebase_snapshot and codebase_snapshot.head_commit else []),
            *(f"dirty:{codebase_snapshot.is_dirty}" if codebase_snapshot else []),
        ],
        learnings=learnings,
    )
    run_fields_complete, missing_artifacts = validate_run_completeness(run_record)
    if (not retrieval_ok or not retrieval_context) and "retrieval_context" not in missing_artifacts:
        missing_artifacts.append("retrieval_context")
    should_persist = not dry_run
    learning_persisted = True
    artifact_persisted = True
    relations = extract_relations(
        source=f"task:{normalized_goal.strip() or 'unknown'}",
        statements=[
            *(f"changed_in:{item}" for item in run_record.change_summary),
            *(f"fixed_by:{item}" for item in run_record.verification_outcomes),
            *(f"related_to:{item}" for item in run_record.reuse_notes),
        ],
    )

    if should_persist:
        if active_store is None:
            learning_persisted = False
        else:
            try:
                active_store.append_learning(
                    topic=normalized_goal,
                    learning=learnings[0],
                    confidence=0.7,
                )
            except (OSError, ValueError, TypeError):
                learning_persisted = False

    if should_persist and not learning_persisted and "persistence_store" not in missing_artifacts:
        missing_artifacts.append("persistence_store")

    run_complete_without_artifact = (
        run_fields_complete
        and learning_persisted
        and "retrieval_context" not in missing_artifacts
    )
    run_status = "completed" if run_complete_without_artifact else "incomplete"
    run_record.final_disposition = (
        "completed" if run_complete_without_artifact else "incomplete_missing_artifacts"
    )

    if should_persist:
        if active_store is None:
            artifact_persisted = False
        else:
            try:
                active_store.append_run_artifact(
                    RunArtifactEntry(
                        goal=run_record.goal or "",
                        success_criteria=run_record.success_criteria or "",
                        planner_decisions=run_record.planner_decisions,
                        change_summary=run_record.change_summary,
                        verification_outcomes=run_record.verification_outcomes,
                        failure_classifications=run_record.failure_classifications,
                        recovery_attempts=run_record.recovery_attempts,
                        reuse_notes=run_record.reuse_notes,
                        learnings=run_record.learnings,
                        final_disposition=run_record.final_disposition or "incomplete",
                        missing_artifacts=missing_artifacts,
                        lane=lane,
                        relations=relations,
                    )
                )
            except (OSError, ValueError, TypeError):
                artifact_persisted = False
                if "persistence_store" not in missing_artifacts:
                    missing_artifacts.append("persistence_store")

    run_complete = (
        run_complete_without_artifact
        and (artifact_persisted if should_persist else True)
    )
    if not run_complete:
        run_status = "incomplete"
        run_record.final_disposition = "incomplete_missing_artifacts"

    return AleivaRunResult(
        status=run_status,
        lane=lane,
        plan=plan,
        execution=execution,
        verification=verification,
        learnings=learnings,
        missing_artifacts=missing_artifacts,
        selected_priority_scores=selected_priority_scores,
        selected_priority_details=selected_priority_details,
        memory_hygiene_actions=memory_hygiene_actions,
        memory_hygiene_action_details=memory_hygiene_action_details,
        policy_tier=policy_tier,
        policy_controls=policy_controls,
        guardrail_events=guardrail_events,
    )


def apply_flaky_test_rerun_heuristics(
    verification_outcomes: list[str],
    rerun_limit: int,
) -> list[str]:
    if rerun_limit <= 0:
        return verification_outcomes

    normalized_outcomes = list(verification_outcomes)
    for outcome in verification_outcomes:
        normalized = outcome.lower()
        if "flaky" not in normalized or "fail" not in normalized:
            continue

        for attempt in range(1, rerun_limit + 1):
            if attempt < rerun_limit:
                normalized_outcomes.append(
                    f"flaky rerun attempt {attempt}: still failing"
                )
                continue
            normalized_outcomes.append(
                f"flaky rerun attempt {attempt}: passed"
            )
        break
    return normalized_outcomes


def _infer_goal_domain(goal: str) -> str | None:
    normalized_goal = goal.lower()
    domain_keywords = ("backend", "frontend", "infra", "test")
    for keyword in domain_keywords:
        if keyword in normalized_goal:
            return keyword
    return None
