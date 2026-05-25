from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LearningEntry:
    topic: str
    learning: str
    confidence: float


class SecondBrainStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def append_learning(self, topic: str, learning: str, confidence: float) -> None:
        entries = self._load_all()
        updated = LearningEntry(
            topic=topic.strip(),
            learning=learning.strip(),
            confidence=confidence,
        )

        deduped_entries: list[LearningEntry] = [
            entry
            for entry in entries
            if not (entry.topic == updated.topic and entry.learning == updated.learning)
        ]
        deduped_entries.append(updated)
        self._write_all(deduped_entries)

    def retrieve(self, topic: str, limit: int) -> list[LearningEntry]:
        if limit <= 0:
            return []

        normalized_topic = topic.strip()
        matching_entries = [
            entry for entry in self._load_all() if entry.topic == normalized_topic
        ]
        return list(reversed(matching_entries))[:limit]

    def _load_all(self) -> list[LearningEntry]:
        loaded: list[LearningEntry] = []
        with self.path.open(encoding="utf-8") as store_file:
            for line in store_file:
                if not line.strip():
                    continue
                payload = json.loads(line)
                loaded.append(
                    LearningEntry(
                        topic=str(payload["topic"]),
                        learning=str(payload["learning"]),
                        confidence=float(payload["confidence"]),
                    )
                )
        return loaded

    def _write_all(self, entries: list[LearningEntry]) -> None:
        with self.path.open("w", encoding="utf-8") as store_file:
            for entry in entries:
                store_file.write(
                    json.dumps(
                        {
                            "topic": entry.topic,
                            "learning": entry.learning,
                            "confidence": entry.confidence,
                        }
                    )
                    + "\n"
                )
