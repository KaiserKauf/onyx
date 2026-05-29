from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class LearningEntry:
    topic: str
    learning: str
    confidence: float
    created_at: float
    contradicts: str | None = None


@dataclass(frozen=True)
class RunArtifactEntry:
    goal: str
    success_criteria: str
    planner_decisions: list[str]
    change_summary: list[str]
    verification_outcomes: list[str]
    failure_classifications: list[str]
    recovery_attempts: list[str]
    reuse_notes: list[str]
    learnings: list[str]
    final_disposition: str
    missing_artifacts: list[str]
    lane: str
    relations: list[tuple[str, str, str]]


class SecondBrainStore:
    def __init__(self, path: Path, create_if_missing: bool = True) -> None:
        self.path = path
        self.run_artifacts_path = path.with_name(f"{path.stem}_runs{path.suffix}")
        if create_if_missing:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.write_text("", encoding="utf-8")
            if not self.run_artifacts_path.exists():
                self.run_artifacts_path.write_text("", encoding="utf-8")

    def append_learning(
        self,
        topic: str,
        learning: str,
        confidence: float,
        contradicts: str | None = None,
    ) -> None:
        entries = self._load_all()
        updated = LearningEntry(
            topic=topic.strip(),
            learning=learning.strip(),
            confidence=confidence,
            created_at=time.time(),
            contradicts=contradicts.strip() if contradicts else None,
        )

        deduped_entries: list[LearningEntry] = [
            entry
            for entry in entries
            if not (entry.topic == updated.topic and entry.learning == updated.learning)
        ]
        deduped_entries.append(updated)
        self._write_all(deduped_entries)

    def retrieve(
        self,
        topic: str,
        limit: int,
        domain: str | None = None,
        relevance_weights: Mapping[str, float] | None = None,
    ) -> list[LearningEntry]:
        if limit <= 0:
            return []

        normalized_topic = topic.strip()
        normalized_domain = domain.strip().lower() if domain else None
        all_entries = self._load_all()
        matching_entries = [
            entry
            for entry in all_entries
            if entry.topic == normalized_topic
            or (
                normalized_domain is not None
                and entry.topic.lower().startswith(f"{normalized_domain}:")
            )
        ]
        non_contradictory_entries = self._filter_contradictions(matching_entries)
        sorted_entries = sorted(
            non_contradictory_entries,
            key=lambda entry: self._ranking_score(
                entry=entry,
                query_topic=normalized_topic,
                domain=normalized_domain,
                relevance_weights=relevance_weights,
            ),
            reverse=True,
        )
        return sorted_entries[:limit]

    def list_learnings(
        self,
        limit: int,
        topic: str | None = None,
        domain: str | None = None,
        relevance_weights: Mapping[str, float] | None = None,
    ) -> list[LearningEntry]:
        if limit <= 0:
            return []

        normalized_topic = topic.strip() if topic else None
        normalized_domain = domain.strip().lower() if domain else None
        loaded_entries = self._load_all()
        filtered_entries = [
            entry
            for entry in loaded_entries
            if normalized_topic is None
            or entry.topic == normalized_topic
            or (
                normalized_domain is not None
                and entry.topic.lower().startswith(f"{normalized_domain}:")
            )
        ]
        sorted_entries = sorted(
            filtered_entries,
            key=lambda entry: self._ranking_score(
                entry=entry,
                query_topic=normalized_topic,
                domain=normalized_domain,
                relevance_weights=relevance_weights,
            ),
            reverse=True,
        )
        return sorted_entries[:limit]

    def apply_scheduled_hygiene(self) -> dict[str, int | list[str]]:
        from onyx.aleiva_core.second_brain.hygiene import run_scheduled_hygiene

        all_entries = self._load_all()
        summary = run_scheduled_hygiene(all_entries)
        self._write_all(summary.entries)
        return {
            "deduplicated_count": summary.deduplicated_count,
            "decay_action_count": summary.decay_action_count,
            "contradiction_guidance": summary.contradiction_guidance,
            "action_count": len(summary.actions),
        }

    def append_run_artifact(self, entry: RunArtifactEntry) -> None:
        self.run_artifacts_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "goal": entry.goal,
            "success_criteria": entry.success_criteria,
            "planner_decisions": entry.planner_decisions,
            "change_summary": entry.change_summary,
            "verification_outcomes": entry.verification_outcomes,
            "failure_classifications": entry.failure_classifications,
            "recovery_attempts": entry.recovery_attempts,
            "reuse_notes": entry.reuse_notes,
            "learnings": entry.learnings,
            "final_disposition": entry.final_disposition,
            "missing_artifacts": entry.missing_artifacts,
            "lane": entry.lane,
            "relations": [list(relation) for relation in entry.relations],
        }
        with self.run_artifacts_path.open("a", encoding="utf-8") as run_artifacts_file:
            run_artifacts_file.write(json.dumps(payload) + "\n")

    def list_run_artifacts(self, limit: int) -> list[RunArtifactEntry]:
        if limit <= 0:
            return []
        if not self.run_artifacts_path.exists():
            return []

        loaded: list[RunArtifactEntry] = []
        with self.run_artifacts_path.open(encoding="utf-8") as run_artifacts_file:
            for line in run_artifacts_file:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    loaded.append(
                        RunArtifactEntry(
                            goal=str(payload["goal"]),
                            success_criteria=str(payload["success_criteria"]),
                            planner_decisions=[str(value) for value in payload["planner_decisions"]],
                            change_summary=[str(value) for value in payload["change_summary"]],
                            verification_outcomes=[
                                str(value) for value in payload["verification_outcomes"]
                            ],
                            failure_classifications=[
                                str(value) for value in payload["failure_classifications"]
                            ],
                            recovery_attempts=[str(value) for value in payload["recovery_attempts"]],
                            reuse_notes=[str(value) for value in payload["reuse_notes"]],
                            learnings=[str(value) for value in payload.get("learnings", [])],
                            final_disposition=str(payload["final_disposition"]),
                            missing_artifacts=[str(value) for value in payload["missing_artifacts"]],
                            lane=str(payload["lane"]),
                            relations=[
                                (
                                    str(relation[0]),
                                    str(relation[1]),
                                    str(relation[2]),
                                )
                                for relation in payload.get("relations", [])
                            ],
                        )
                    )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError, IndexError):
                    continue
        return list(reversed(loaded))[:limit]

    def _load_all(self) -> list[LearningEntry]:
        loaded: list[LearningEntry] = []
        if not self.path.exists():
            return loaded
        with self.path.open(encoding="utf-8") as store_file:
            for line in store_file:
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    loaded.append(
                        LearningEntry(
                            topic=str(payload["topic"]),
                            learning=str(payload["learning"]),
                            confidence=float(payload["confidence"]),
                            created_at=float(payload.get("created_at", 0.0)),
                            contradicts=(
                                str(payload["contradicts"])
                                if payload.get("contradicts") is not None
                                else None
                            ),
                        ),
                    )
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    continue
        return loaded

    def _write_all(self, entries: list[LearningEntry]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as store_file:
            for entry in entries:
                store_file.write(
                    json.dumps(
                        {
                            "topic": entry.topic,
                            "learning": entry.learning,
                            "confidence": entry.confidence,
                            "created_at": entry.created_at,
                            "contradicts": entry.contradicts,
                        }
                    )
                    + "\n"
                )

    def _ranking_score(
        self,
        entry: LearningEntry,
        query_topic: str | None = None,
        domain: str | None = None,
        relevance_weights: Mapping[str, float] | None = None,
    ) -> float:
        age_seconds = max(0.0, time.time() - entry.created_at)
        age_days = age_seconds / 86400.0
        freshness_multiplier = max(0.5, 1.0 - (age_days / 30.0))
        score = entry.confidence * freshness_multiplier
        if query_topic is not None and entry.topic == query_topic:
            score += 0.2
        if domain is not None and entry.topic.lower().startswith(f"{domain}:"):
            score += 0.15
        if relevance_weights:
            score += self._domain_relevance_bonus(entry.topic, relevance_weights)
        return score

    def _domain_relevance_bonus(
        self,
        topic: str,
        relevance_weights: Mapping[str, float],
    ) -> float:
        topic_normalized = topic.lower()
        best_bonus = 0.0
        for key, weight in relevance_weights.items():
            if not isinstance(weight, (int, float)) or weight <= 0:
                continue
            normalized_key = key.strip().lower()
            if not normalized_key:
                continue
            if topic_normalized == normalized_key or topic_normalized.startswith(
                f"{normalized_key}:"
            ):
                best_bonus = max(best_bonus, float(weight))
        return best_bonus

    def _filter_contradictions(self, entries: list[LearningEntry]) -> list[LearningEntry]:
        best_by_key: dict[tuple[str, str], float] = {}
        for entry in entries:
            key = (entry.topic, entry.learning)
            best_by_key[key] = max(
                best_by_key.get(key, 0.0),
                self._ranking_score(entry=entry),
            )

        seen_pairs: set[tuple[tuple[str, str], tuple[str, str]]] = set()
        blocked_keys: set[tuple[str, str]] = set()
        for entry in entries:
            entry_key = (entry.topic, entry.learning)
            contradicted_key = (entry.topic, entry.contradicts or "")
            if not entry.contradicts or contradicted_key not in best_by_key:
                continue
            pair = tuple(sorted((entry_key, contradicted_key)))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            entry_score = best_by_key[entry_key]
            contradicted_score = best_by_key[contradicted_key]
            if entry_score > contradicted_score:
                blocked_keys.add(contradicted_key)
            elif contradicted_score > entry_score:
                blocked_keys.add(entry_key)
            else:
                winner_key = min(entry_key, contradicted_key)
                loser_key = contradicted_key if winner_key == entry_key else entry_key
                blocked_keys.add(loser_key)

        filtered: list[LearningEntry] = []
        for entry in entries:
            if (entry.topic, entry.learning) in blocked_keys:
                continue
            filtered.append(entry)
        return filtered
