#!/usr/bin/env python3
"""Queue Cursor session learnings for Aleiva second-brain ingest (stop hook)."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _repo_root() -> Path:
    env_root = os.environ.get("ALEIVA_REPO_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()
    return Path.cwd().resolve()


def _queue_path(root: Path) -> Path:
    queue_dir = root / "backend" / ".aleiva"
    queue_dir.mkdir(parents=True, exist_ok=True)
    return queue_dir / "cursor_learning_queue.jsonl"


def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    status = str(payload.get("status", "")).strip()
    if status and status not in {"completed", "aborted", "error"}:
        return

    conversation = payload.get("conversation")
    summary = ""
    if isinstance(conversation, list) and conversation:
        last = conversation[-1]
        if isinstance(last, dict):
            summary = str(last.get("text") or last.get("content") or "").strip()
    if not summary:
        summary = str(payload.get("reason") or payload.get("message") or "").strip()
    if not summary:
        return

    platform_id = os.environ.get("ALEIVA_PLATFORM_ID", "aleivaos").strip() or "aleivaos"
    entry = {
        "topic": f"{platform_id}: cursor_session",
        "learning": summary[:2000],
        "confidence": 0.55,
        "platform_id": platform_id,
        "captured_at": time.time(),
        "source": "cursor_stop_hook",
    }
    queue_file = _queue_path(_repo_root())
    with queue_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
