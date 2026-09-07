"""
Aleiva periodic memory hygiene Celery tasks.

Beat registration (opt-in, non-breaking):
  Set ALEIVA_MEMORY_HYGIENE_SCHEDULE_ENABLED=true to add the hourly beat entry in
  `onyx.background.celery.tasks.beat_schedule`.

Manual invocation:
  aleiva_memory_hygiene_task.apply_async(expires=900)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from celery import shared_task
from celery import Task

from onyx.configs.constants import OnyxCeleryTask
from onyx.utils.logger import setup_logger

logger = setup_logger()

_ALEIVA_STORE_DIR = Path(__file__).resolve().parents[6] / ".aleiva"


@shared_task(
    name=OnyxCeleryTask.ALEIVA_MEMORY_HYGIENE_TASK,
    ignore_result=True,
    bind=True,
    trail=False,
)
def aleiva_memory_hygiene_task(self: Task, **kwargs: Any) -> None:  # noqa: ARG001
    """
    Periodic second-brain hygiene for Aleiva stores under `.aleiva/`.

    Iterates known per-user store files and applies scheduled deduplication,
    decay, and contradiction guidance. Safe to run while the API is active;
    each store file is processed independently.
    """
    from onyx.aleiva_core.second_brain.store import SecondBrainStore

    if not _ALEIVA_STORE_DIR.exists():
        logger.info("Aleiva memory hygiene skipped: store directory missing")
        return

    store_paths = sorted(_ALEIVA_STORE_DIR.glob("second_brain_*.jsonl"))
    if not store_paths:
        logger.info("Aleiva memory hygiene skipped: no second-brain stores found")
        return

    processed = 0
    for store_path in store_paths:
        try:
            store = SecondBrainStore(store_path, create_if_missing=False)
            summary = store.apply_scheduled_hygiene()
            processed += 1
            logger.info(
                "Aleiva memory hygiene applied",
                extra={
                    "store": store_path.name,
                    "action_count": summary.get("action_count", 0),
                },
            )
        except OSError:
            logger.warning(
                "Aleiva memory hygiene failed for store",
                extra={"store": store_path.name},
            )

    logger.info(
        "Aleiva memory hygiene sweep complete",
        extra={"stores_processed": processed, "stores_found": len(store_paths)},
    )
