from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Literal

DEFAULT_ALLOW_PREFIXES: tuple[str, ...] = (
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
)

DEFAULT_BLOCKED_PATTERNS: tuple[str, ...] = (
    r"git\s+reset\s+--hard",
    r"git\s+push\s+--force(?:-with-lease)?",
    r"git\s+checkout\s+--",
    r"git\s+clean\s+-[a-zA-Z]*f[a-zA-Z]*d",
    r"(?:^|\s)rm\s+-rf\s+/",
    r"(?:^|\s)del\s+/[sq]\s+/[sq]",
)

DEFAULT_POLICY_CONFIG_PATH = Path(__file__).with_name("policy_config.json")
PolicyTier = Literal["safe", "normal", "experimental"]

DEFAULT_TIER_LIMITS: dict[PolicyTier, dict[str, int]] = {
    "safe": {
        "max_commands_per_run": 5,
        "max_timeout_seconds": 20,
    },
    "normal": {
        "max_commands_per_run": 12,
        "max_timeout_seconds": 45,
    },
    "experimental": {
        "max_commands_per_run": 20,
        "max_timeout_seconds": 120,
    },
}


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class TierLimits:
    max_commands_per_run: int
    max_timeout_seconds: int


class AleivaPolicy:
    def __init__(
        self,
        tier: PolicyTier,
        allow_prefixes: tuple[str, ...],
        blocked_patterns: tuple[str, ...],
        tier_limits: TierLimits,
    ) -> None:
        self.tier = tier
        self.allow_prefixes = allow_prefixes
        self.blocked_patterns = blocked_patterns
        self.tier_limits = tier_limits

    @classmethod
    def default(cls, tier: PolicyTier = "normal") -> "AleivaPolicy":
        config = _load_policy_config()
        allow_prefixes = _load_string_tuple(config, "allow_prefixes")
        blocked_patterns = _load_string_tuple(config, "blocked_patterns")
        tier_limits = _load_tier_limits(config, tier=tier) or _default_tier_limits(tier)
        return cls(
            tier=tier,
            allow_prefixes=allow_prefixes or DEFAULT_ALLOW_PREFIXES,
            blocked_patterns=blocked_patterns or DEFAULT_BLOCKED_PATTERNS,
            tier_limits=tier_limits,
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

    def describe_controls(self) -> dict[str, int | str]:
        return {
            "tier": self.tier,
            "max_commands_per_run": self.tier_limits.max_commands_per_run,
            "max_timeout_seconds": self.tier_limits.max_timeout_seconds,
        }


def _load_policy_config() -> dict[str, Any] | None:
    try:
        config_content = DEFAULT_POLICY_CONFIG_PATH.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        config = json.loads(config_content)
    except json.JSONDecodeError:
        return None

    if not isinstance(config, dict):
        return None

    return config


def _load_string_tuple(config: dict[str, Any] | None, field_name: str) -> tuple[str, ...] | None:
    if config is None:
        return None

    values = config.get(field_name)
    if not isinstance(values, list):
        return None

    normalized_values: list[str] = []
    for value in values:
        if not isinstance(value, str):
            return None
        normalized_value = value.strip()
        if not normalized_value:
            return None
        normalized_values.append(normalized_value)

    if not normalized_values:
        return None

    return tuple(normalized_values)


def _default_tier_limits(tier: PolicyTier) -> TierLimits:
    limits = DEFAULT_TIER_LIMITS[tier]
    return TierLimits(
        max_commands_per_run=limits["max_commands_per_run"],
        max_timeout_seconds=limits["max_timeout_seconds"],
    )


def _load_tier_limits(config: dict[str, Any] | None, tier: PolicyTier) -> TierLimits | None:
    if config is None:
        return None
    tiers = config.get("tiers")
    if not isinstance(tiers, dict):
        return None
    tier_config = tiers.get(tier)
    if not isinstance(tier_config, dict):
        return None

    max_commands_per_run = tier_config.get("max_commands_per_run")
    max_timeout_seconds = tier_config.get("max_timeout_seconds")
    if not isinstance(max_commands_per_run, int) or max_commands_per_run <= 0:
        return None
    if not isinstance(max_timeout_seconds, int) or max_timeout_seconds <= 0:
        return None
    return TierLimits(
        max_commands_per_run=max_commands_per_run,
        max_timeout_seconds=max_timeout_seconds,
    )
