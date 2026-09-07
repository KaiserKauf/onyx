from pydantic import BaseModel
from pydantic import Field


class AleivaRunRecord(BaseModel):
    goal: str | None = None
    success_criteria: str | None = None
    planner_decisions: list[str] = Field(default_factory=list)
    change_summary: list[str] = Field(default_factory=list)
    verification_outcomes: list[str] = Field(default_factory=list)
    failure_classifications: list[str] = Field(default_factory=list)
    recovery_attempts: list[str] = Field(default_factory=list)
    reuse_notes: list[str] = Field(default_factory=list)
    deferred_critical_issues: list[str] = Field(default_factory=list)
    unresolved_critical_issues: list[str] = Field(default_factory=list)
    final_disposition: str | None = None
    learnings: list[str] = Field(default_factory=list)
    codebase_context: list[str] = Field(default_factory=list)
    files_changed: list[str] = Field(default_factory=list)
