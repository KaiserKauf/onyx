#!/usr/bin/env python3
"""Aleiva git safety guard for Cursor beforeShellExecution hooks."""

from __future__ import annotations

import json
import re
import sys

# (pattern, user_message) — order matters: first match wins.
_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"git\s+reset\b.*--hard", re.I),
        "Aleiva policy blocks `git reset --hard`.",
    ),
    (
        re.compile(r"git\s+push\b.*(?:--force|-f)\b", re.I),
        "Aleiva policy blocks force push.",
    ),
    (
        re.compile(r"git\s+clean\b.*(?:-f|-x)", re.I),
        "Aleiva policy blocks destructive `git clean`.",
    ),
    (
        re.compile(r"git\s+checkout\b.*--\s", re.I),
        "Aleiva policy blocks discarding working tree via checkout.",
    ),
    (
        re.compile(r"git\s+restore\b.*--(?:hard|source)", re.I),
        "Aleiva policy blocks hard restore.",
    ),
    (
        re.compile(r"git\s+config\b", re.I),
        "Aleiva policy blocks `git config` changes.",
    ),
    (
        re.compile(r"git\s+commit\b.*--no-verify", re.I),
        "Aleiva policy blocks skipping git hooks.",
    ),
    (
        re.compile(
            r"git\s+branch\b.*-[dD]\b.*\b(?:main|master)\b", re.I
        ),
        "Aleiva policy blocks deleting protected branches.",
    ),
]


def _emit(permission: str, user_message: str | None = None, agent_message: str | None = None) -> None:
    payload: dict[str, str] = {"permission": permission}
    if user_message:
        payload["user_message"] = user_message
    if agent_message:
        payload["agent_message"] = agent_message
    sys.stdout.write(json.dumps(payload))


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        _emit("allow")
        return

    command = data.get("command", "")
    if not isinstance(command, str):
        command = str(command)

    for pattern, message in _RULES:
        if pattern.search(command):
            _emit(
                "deny",
                user_message=message,
                agent_message=f"Hook blocked: {command[:500]}",
            )
            return

    _emit("allow")


if __name__ == "__main__":
    main()
