from onyx.aleiva_core.types import AleivaRunRecord


def validate_run_completeness(run: AleivaRunRecord) -> tuple[bool, list[str]]:
    missing_fields: list[str] = []

    if not _has_text(run.goal):
        missing_fields.append("goal")
    if not _has_text(run.success_criteria):
        missing_fields.append("success_criteria")
    if not _has_non_empty_entries(run.planner_decisions):
        missing_fields.append("planner_decisions")
    if not _has_non_empty_entries(run.change_summary):
        missing_fields.append("change_summary")
    if not _has_non_empty_entries(run.verification_outcomes):
        missing_fields.append("verification_outcomes")
    if not _has_non_empty_entries(run.failure_classifications):
        missing_fields.append("failure_classifications")
    if not _has_non_empty_entries(run.recovery_attempts):
        missing_fields.append("recovery_attempts")
    if not _has_non_empty_entries(run.reuse_notes):
        missing_fields.append("reuse_notes")
    if not _has_text(run.final_disposition):
        missing_fields.append("final_disposition")
    if not _has_non_empty_learning(run.learnings):
        missing_fields.append("learnings")
    if run.files_changed and not _has_non_empty_entries(run.files_changed):
        missing_fields.append("files_changed")
    if run.codebase_context and not _has_non_empty_entries(run.codebase_context):
        missing_fields.append("codebase_context")
    if _has_unresolved_critical_issues(run):
        missing_fields.append("unresolved_critical_issues")

    return len(missing_fields) == 0, missing_fields


def _has_text(value: str | None) -> bool:
    return value is not None and bool(value.strip())


def _has_non_empty_learning(learnings: list[object] | None) -> bool:
    if not learnings:
        return False
    return any(isinstance(learning, str) and bool(learning.strip()) for learning in learnings)


def _has_non_empty_entries(entries: list[object] | None) -> bool:
    if not entries:
        return False
    return any(isinstance(entry, str) and bool(entry.strip()) for entry in entries)


def _has_unresolved_critical_issues(run: AleivaRunRecord) -> bool:
    unresolved_issues = {
        issue.strip()
        for issue in run.unresolved_critical_issues
        if isinstance(issue, str) and issue.strip()
    }
    deferred_issues = {
        issue.strip()
        for issue in run.deferred_critical_issues
        if isinstance(issue, str) and issue.strip()
    }
    return bool(unresolved_issues.difference(deferred_issues))
