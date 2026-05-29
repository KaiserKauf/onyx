import json
import subprocess
from pathlib import Path

from pytest import MonkeyPatch

from onyx.aleiva_core import policy as policy_module
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
    assert result.tier == "normal"
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
    assert result.tier == "normal"
    assert result.exit_code == 0
    assert result.stdout == "ok"


def test_policy_loads_defaults_from_config(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    config_path = tmp_path / "policy_config_test.json"
    config_path.write_text(
        json.dumps(
            {
                "version": 1,
                "allow_prefixes": ["echo "],
                "blocked_patterns": [r"git\s+reset\s+--hard"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(policy_module, "DEFAULT_POLICY_CONFIG_PATH", config_path)

    policy = AleivaPolicy.default()
    decision = policy.evaluate_command("echo hello")

    assert decision.allowed is True
    assert decision.reason == "allowed"

def test_policy_falls_back_when_config_is_invalid(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    config_path = tmp_path / "policy_config_test.json"
    config_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(policy_module, "DEFAULT_POLICY_CONFIG_PATH", config_path)

    policy = AleivaPolicy.default()

    assert policy.evaluate_command("pytest backend/tests/unit -q").allowed is True
    assert policy.evaluate_command("echo hello").reason == "not_allowlisted"


def test_policy_tier_limits_apply_to_runtime_execution() -> None:
    limited = execute_with_policy(
        command="pytest backend/tests/unit -q",
        tier="safe",
        command_index=6,
    )

    assert limited.allowed is False
    assert limited.reason == "tier_command_limit_exceeded"
    assert limited.tier == "safe"


def test_policy_tier_timeout_limit_blocks_excessive_timeout() -> None:
    limited = execute_with_policy(
        command="pytest backend/tests/unit -q",
        tier="safe",
        timeout_seconds=60,
    )

    assert limited.allowed is False
    assert limited.reason == "tier_timeout_limit_exceeded"
    assert limited.tier == "safe"


def test_policy_loads_tier_limits_from_config() -> None:
    safe_policy = AleivaPolicy.default(tier="safe")
    experimental_policy = AleivaPolicy.default(tier="experimental")

    assert safe_policy.tier_limits.max_commands_per_run == 5
    assert safe_policy.tier_limits.max_timeout_seconds == 20
    assert experimental_policy.tier_limits.max_commands_per_run == 20
    assert experimental_policy.tier_limits.max_timeout_seconds == 120

