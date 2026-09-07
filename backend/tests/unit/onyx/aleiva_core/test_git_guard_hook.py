"""Cursor git hook stays aligned with AleivaPolicy for destructive git commands."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from onyx.aleiva_core.policy import AleivaPolicy

_REPO_ROOT = Path(__file__).resolve().parents[5]
_HOOK_SCRIPT = _REPO_ROOT / ".cursor" / "hooks" / "aleiva-guard-git.py"

_POLICY_BLOCKED_GIT = (
    "git reset --hard HEAD",
    "git push --force origin main",
    "git push -f origin feat-aleiva-mvp",
    "git clean -fdx",
    "git checkout -- backend/onyx/aleiva_core/policy.py",
)

_POLICY_ALLOWED_GIT = (
    "git status",
    "git diff HEAD",
    "git show HEAD",
)


def _run_hook(command: str) -> dict[str, str]:
    assert _HOOK_SCRIPT.is_file(), f"missing hook script: {_HOOK_SCRIPT}"
    completed = subprocess.run(
        [sys.executable, str(_HOOK_SCRIPT)],
        input=json.dumps({"command": command}),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_hook_script_exists() -> None:
    assert _HOOK_SCRIPT.is_file()


def test_hook_and_policy_both_block_destructive_git() -> None:
    policy = AleivaPolicy.default()
    for command in _POLICY_BLOCKED_GIT:
        decision = policy.evaluate_command(command)
        assert decision.allowed is False
        assert decision.reason == "blocked_pattern"
        hook = _run_hook(command)
        assert hook["permission"] == "deny"


def test_hook_and_policy_both_allow_readonly_git() -> None:
    policy = AleivaPolicy.default()
    for command in _POLICY_ALLOWED_GIT:
        assert policy.evaluate_command(command).allowed is True
        hook = _run_hook(command)
        assert hook["permission"] == "allow"


def test_hook_blocks_git_config_even_when_not_allowlisted() -> None:
    command = "git config user.email attacker@example.com"
    policy = AleivaPolicy.default()
    assert policy.evaluate_command(command).allowed is False
    assert policy.evaluate_command(command).reason == "not_allowlisted"
    hook = _run_hook(command)
    assert hook["permission"] == "deny"
