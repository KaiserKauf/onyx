from pathlib import Path

from onyx.aleiva_core.codebase_snapshot import capture_codebase_snapshot
from onyx.aleiva_core.codebase_snapshot import CodebaseSnapshotStore


def test_capture_codebase_snapshot_from_git_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    snapshot = capture_codebase_snapshot(repo_path=repo, platform_id="vulty")
    assert snapshot.repo_path == str(repo.resolve())
    assert isinstance(snapshot.is_dirty, bool)
    assert isinstance(snapshot.changed_files, list)


def test_snapshot_store_roundtrip(tmp_path: Path) -> None:
    store_path = tmp_path / "snapshots.jsonl"
    store = CodebaseSnapshotStore(store_path)
    snapshot = capture_codebase_snapshot(
        repo_path=tmp_path,
        platform_id="aleivaos",
        run_id="test-run",
    )
    store.append(snapshot)
    loaded = store.list_snapshots(limit=5)
    assert len(loaded) == 1
    assert loaded[0].platform_id == "aleivaos"
    assert loaded[0].run_id == "test-run"


def test_snapshot_filters_secret_like_paths() -> None:
    from onyx.aleiva_core.codebase_snapshot import _sanitize_changed_files

    changed = _sanitize_changed_files(
        [
            " M .env",
            " M backend/onyx/aleiva_core/platforms.py",
            "?? credentials.json",
        ]
    )
    assert ".env" not in changed
    assert "credentials.json" not in changed
    assert "backend/onyx/aleiva_core/platforms.py" in changed
