from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


class AleivaPolicy:
    def __init__(
        self,
        allow_prefixes: tuple[str, ...],
        blocked_patterns: tuple[str, ...],
    ) -> None:
        self.allow_prefixes = allow_prefixes
        self.blocked_patterns = blocked_patterns

    @classmethod
    def default(cls) -> "AleivaPolicy":
        return cls(
            allow_prefixes=(
                "pytest ",
                "uv run pytest ",
                "ruff ",
                "uv run ruff ",
                "mypy ",
                "uv run mypy ",
                "python ",
                "uv run python ",
                "git status",
                "git diff",
                "git show",
            ),
            blocked_patterns=(
                r"git\s+reset\s+--hard",
                r"git\s+push\s+--force(?:-with-lease)?",
                r"git\s+checkout\s+--",
                r"git\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*d",
                r"(?:^|\s)rm\s+-rf\s+/",
                r"(?:^|\s)del\s+/[sq]\s+/[sq]",
            ),
        )

    def evaluate_command(self, command: str) -> PolicyDecision:
        normalized_command = command.strip()
        if not normalized_command:
            return PolicyDecision(allowed=False, reason="empty_command")

        for blocked_pattern in self.blocked_patterns:
            if re.search(blocked_pattern, normalized_command):
                return PolicyDecision(allowed=False, reason="blocked_pattern")

        if any(normalized_command.startswith(prefix) for prefix in self.allow_prefixes):
            return PolicyDecision(allowed=True, reason="allowed")

        return PolicyDecision(allowed=False, reason="not_allowlisted")
