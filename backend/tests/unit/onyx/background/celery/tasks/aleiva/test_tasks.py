from pathlib import Path
from unittest.mock import patch

from onyx.background.celery.tasks.aleiva.tasks import aleiva_memory_hygiene_task


def test_aleiva_memory_hygiene_task_skips_when_store_dir_missing(tmp_path: Path) -> None:
    missing_dir = tmp_path / "missing_aleiva"

    with patch(
        "onyx.background.celery.tasks.aleiva.tasks._ALEIVA_STORE_DIR",
        missing_dir,
    ):
        aleiva_memory_hygiene_task.run()


def test_aleiva_memory_hygiene_task_processes_existing_stores(tmp_path: Path) -> None:
    store_dir = tmp_path / "aleiva"
    store_dir.mkdir()
    store_path = store_dir / "second_brain_user1.jsonl"
    store_path.write_text(
        '{"topic":"goal","learning":"reuse scoped changes","confidence":0.7,"created_at":1.0}\n',
        encoding="utf-8",
    )

    with patch(
        "onyx.background.celery.tasks.aleiva.tasks._ALEIVA_STORE_DIR",
        store_dir,
    ):
        aleiva_memory_hygiene_task.run()

    assert store_path.exists()
