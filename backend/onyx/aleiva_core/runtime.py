from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from onyx.aleiva_core.policy import AleivaPolicy
from onyx.aleiva_core.policy import PolicyTier


@dataclass(frozen=True)
class RuntimeExecutionResult:
    allowed: bool
    reason: str
    command: str
    tier: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[str, int | None], subprocess.CompletedProcess[str]]


def execute_with_policy(
    command: str,
    policy: AleivaPolicy | None = None,
    tier: PolicyTier = "normal",
    command_index: int = 1,
    timeout_seconds: int | None = 30,
    runner: CommandRunner | None = None,
) -> RuntimeExecutionResult:
    active_policy = policy or AleivaPolicy.default(tier=tier)
    if command_index > active_policy.tier_limits.max_commands_per_run:
        return RuntimeExecutionResult(
            allowed=False,
            reason="tier_command_limit_exceeded",
            command=command,
            tier=active_policy.tier,
        )
    if timeout_seconds is not None and timeout_seconds > active_policy.tier_limits.max_timeout_seconds:
        return RuntimeExecutionResult(
            allowed=False,
            reason="tier_timeout_limit_exceeded",
            command=command,
            tier=active_policy.tier,
        )
    decision = active_policy.evaluate_command(command)
    if not decision.allowed:
        return RuntimeExecutionResult(
            allowed=False,
            reason=decision.reason,
            command=command,
            tier=active_policy.tier,
        )

    active_runner = runner or _default_runner
    try:
        process = active_runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return RuntimeExecutionResult(
            allowed=False,
            reason="timeout",
            command=command,
            tier=active_policy.tier,
        )

    return RuntimeExecutionResult(
        allowed=True,
        reason="executed",
        command=command,
        tier=active_policy.tier,
        exit_code=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def _default_runner(command: str, timeout_seconds: int | None) -> subprocess.CompletedProcess[str]:
    command_parts = shlex.split(command, posix=False)
    return subprocess.run(
        command_parts,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
