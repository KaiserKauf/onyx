from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from onyx.aleiva_core.policy import AleivaPolicy


@dataclass(frozen=True)
class RuntimeExecutionResult:
    allowed: bool
    reason: str
    command: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[str, int | None], subprocess.CompletedProcess[str]]


def execute_with_policy(
    command: str,
    policy: AleivaPolicy | None = None,
    timeout_seconds: int | None = 30,
    runner: CommandRunner | None = None,
) -> RuntimeExecutionResult:
    active_policy = policy or AleivaPolicy.default()
    decision = active_policy.evaluate_command(command)
    if not decision.allowed:
        return RuntimeExecutionResult(
            allowed=False,
            reason=decision.reason,
            command=command,
        )

    active_runner = runner or _default_runner
    try:
        process = active_runner(command, timeout_seconds)
    except subprocess.TimeoutExpired:
        return RuntimeExecutionResult(
            allowed=False,
            reason="timeout",
            command=command,
        )

    return RuntimeExecutionResult(
        allowed=True,
        reason="executed",
        command=command,
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
