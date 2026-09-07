from __future__ import annotations

import json
import subprocess
import time
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path

_MAX_CHANGED_FILES = 50
_SECRET_PATTERNS = (".env", "credentials", "secret", "password", "api_key")


@dataclass(frozen=True)
class CodebaseSnapshot:
    repo_path: str
    branch: str | None
    head_commit: str | None
    is_dirty: bool
    changed_files: list[str]
    run_id: str | None
    platform_id: str | None
    captured_at: float
    test_summary: str | None = None


def capture_codebase_snapshot(
    repo_path: Path | None = None,
    *,
    run_id: str | None = None,
    platform_id: str | None = None,
    test_summary: str | None = None,
) -> CodebaseSnapshot:
    resolved_path = (repo_path or Path.cwd()).resolve()
    branch = _git_output(["git", "-C", str(resolved_path), "rev-parse", "--abbrev-ref", "HEAD"])
    head_commit = _git_output(["git", "-C", str(resolved_path), "rev-parse", "HEAD"])
    status_lines = _git_output_lines(
        ["git", "-C", str(resolved_path), "status", "--porcelain"]
    )
    changed_files = _sanitize_changed_files(status_lines)
    return CodebaseSnapshot(
        repo_path=str(resolved_path),
        branch=branch,
        head_commit=head_commit,
        is_dirty=bool(changed_files),
        changed_files=changed_files,
        run_id=run_id,
        platform_id=platform_id,
        captured_at=time.time(),
        test_summary=test_summary,
    )


class CodebaseSnapshotStore:
    def __init__(self, path: Path, create_if_missing: bool = True) -> None:
        self.path = path
        if create_if_missing:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.write_text("", encoding="utf-8")

    def append(self, snapshot: CodebaseSnapshot) -> None:
        record = asdict(snapshot)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    def list_snapshots(self, limit: int = 20) -> list[CodebaseSnapshot]:
        if limit <= 0 or not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        snapshots: list[CodebaseSnapshot] = []
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            snapshots.append(
                CodebaseSnapshot(
                    repo_path=str(payload.get("repo_path", "")),
                    branch=payload.get("branch"),
                    head_commit=payload.get("head_commit"),
                    is_dirty=bool(payload.get("is_dirty")),
                    changed_files=[
                        str(item)
                        for item in payload.get("changed_files", [])
                        if isinstance(item, str)
                    ],
                    run_id=payload.get("run_id"),
                    platform_id=payload.get("platform_id"),
                    captured_at=float(payload.get("captured_at", 0.0)),
                    test_summary=payload.get("test_summary"),
                )
            )
            if len(snapshots) >= limit:
                break
        return snapshots


def _git_output(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    value = completed.stdout.strip()
    return value or None


def _git_output_lines(command: list[str]) -> list[str]:
    value = _git_output(command)
    if not value:
        return []
    return [line for line in value.splitlines() if line.strip()]


def _sanitize_changed_files(status_lines: list[str]) -> list[str]:
    changed: list[str] = []
    for line in status_lines:
        if len(line) < 4:
            continue
        file_path = line[3:].strip()
        if not file_path or _looks_like_secret_path(file_path):
            continue
        changed.append(file_path)
        if len(changed) >= _MAX_CHANGED_FILES:
            break
    return changed


def _looks_like_secret_path(file_path: str) -> bool:
    lowered = file_path.lower()
    return any(pattern in lowered for pattern in _SECRET_PATTERNS)
