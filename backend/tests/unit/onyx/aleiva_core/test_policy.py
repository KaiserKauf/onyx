import subprocess

from onyx.aleiva_core.policy import AleivaPolicy
from onyx.aleiva_core.runtime import execute_with_policy


def test_policy_blocks_destructive_git() -> None:
    policy = AleivaPolicy.default()
    decision = policy.evaluate_command("git reset --hard")

    assert decision.allowed is False
    assert decision.reason == "blocked_pattern"


def test_policy_allows_pytest_command() -> None:
    policy = AleivaPolicy.default()
    decision = policy.evaluate_command("pytest backend/tests/unit -q")

    assert decision.allowed is True
    assert decision.reason == "allowed"


def test_policy_rejects_non_allowlisted_command() -> None:
    policy = AleivaPolicy.default()
    decision = policy.evaluate_command("echo hello")

    assert decision.allowed is False
    assert decision.reason == "not_allowlisted"


def test_runtime_denies_blocked_command_without_execution() -> None:
    calls: list[str] = []

    def _runner(command: str, _timeout_seconds: int | None) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    result = execute_with_policy(
        command="git push --force",
        policy=AleivaPolicy.default(),
        runner=_runner,
    )

    assert result.allowed is False
    assert result.reason == "blocked_pattern"
    assert calls == []


def test_runtime_executes_allowlisted_command() -> None:
    def _runner(command: str, timeout_seconds: int | None) -> subprocess.CompletedProcess[str]:
        assert command == "pytest backend/tests/unit -q"
        assert timeout_seconds == 30
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

    result = execute_with_policy(
        command="pytest backend/tests/unit -q",
        policy=AleivaPolicy.default(),
        runner=_runner,
    )

    assert result.allowed is True
    assert result.reason == "executed"
    assert result.exit_code == 0
    assert result.stdout == "ok"
