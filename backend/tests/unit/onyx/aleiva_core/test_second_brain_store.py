from pathlib import Path

from onyx.aleiva_core.second_brain.graph import extract_relations
from onyx.aleiva_core.second_brain.store import RunArtifactEntry
from onyx.aleiva_core.second_brain.store import SecondBrainStore


def test_store_persists_and_reads_latest(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("parser", "Prefer helper extraction", confidence=0.7)

    results = store.retrieve("parser", limit=5)
    assert len(results) == 1
    assert results[0].learning == "Prefer helper extraction"
    assert results[0].confidence == 0.7
    assert results[0].created_at > 0


def test_store_dedups_same_learning(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("parser", "Prefer helper extraction", confidence=0.7)
    store.append_learning("parser", "Prefer helper extraction", confidence=0.9)

    results = store.retrieve("parser", limit=5)
    assert len(results) == 1
    assert results[0].confidence == 0.9


def test_extract_relations_recognizes_known_relation_labels() -> None:
    relations = extract_relations(
        source="task:parser",
        statements=[
            "depends_on:file:parser_helper.py",
            "fixed_by:test:test_parser.py",
            "general cleanup note",
        ],
    )

    assert ("task:parser", "depends_on", "file:parser_helper.py") in relations
    assert ("task:parser", "fixed_by", "test:test_parser.py") in relations
    assert ("task:parser", "related_to", "general cleanup note") in relations


def test_store_persists_run_artifacts(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_run_artifact(
        RunArtifactEntry(
            goal="Refactor parser",
            success_criteria="Targeted checks pass",
            planner_decisions=["Do incremental edits first"],
            change_summary=["Updated parser helper extraction path"],
            verification_outcomes=["Unit tests pass"],
            failure_classifications=["none"],
            recovery_attempts=["none required"],
            reuse_notes=["Applied prior parser learning"],
            learnings=["Prefer helper extraction for parser updates"],
            final_disposition="completed",
            missing_artifacts=[],
            lane="balanced",
            relations=[("task:parser", "changed_in", "parser.py")],
        )
    )

    entries = store.list_run_artifacts(limit=1)
    assert len(entries) == 1
    assert entries[0].goal == "Refactor parser"
    assert entries[0].final_disposition == "completed"
    assert entries[0].planner_decisions
    assert entries[0].learnings == ["Prefer helper extraction for parser updates"]
    assert entries[0].relations == [("task:parser", "changed_in", "parser.py")]


def test_store_skips_contradicted_learning_when_stronger_base_exists(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("parser", "Use helper extraction", confidence=0.9)
    store.append_learning(
        "parser",
        "Inline parsing logic",
        confidence=0.5,
        contradicts="Use helper extraction",
    )

    entries = store.retrieve("parser", limit=5)
    learnings = [entry.learning for entry in entries]
    assert "Use helper extraction" in learnings
    assert "Inline parsing logic" not in learnings


def test_store_returns_only_one_side_of_contradiction_pair(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("parser", "Use helper extraction", confidence=0.7)
    store.append_learning(
        "parser",
        "Inline parsing logic",
        confidence=0.9,
        contradicts="Use helper extraction",
    )

    entries = store.retrieve("parser", limit=5)
    learnings = [entry.learning for entry in entries]
    assert ("Use helper extraction" in learnings) != ("Inline parsing logic" in learnings)


def test_store_ignores_malformed_learning_rows(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.path.write_text('{"topic":"parser"}\n{not-json}\n', encoding="utf-8")
    store.append_learning("parser", "Prefer helper extraction", confidence=0.8)

    results = store.retrieve("parser", limit=5)
    assert len(results) == 1
    assert results[0].learning == "Prefer helper extraction"


def test_store_ignores_malformed_run_artifact_rows(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.run_artifacts_path.write_text('{"goal":"parser"}\n{not-json}\n', encoding="utf-8")
    store.append_run_artifact(
        RunArtifactEntry(
            goal="Refactor parser",
            success_criteria="Targeted checks pass",
            planner_decisions=["Do incremental edits first"],
            change_summary=["Updated parser helper extraction path"],
            verification_outcomes=["Unit tests pass"],
            failure_classifications=["none"],
            recovery_attempts=["none required"],
            reuse_notes=["Applied prior parser learning"],
            learnings=["Prefer helper extraction for parser updates"],
            final_disposition="completed",
            missing_artifacts=[],
            lane="balanced",
            relations=[("task:parser", "changed_in", "parser.py")],
        )
    )

    entries = store.list_run_artifacts(limit=5)
    assert len(entries) == 1
    assert entries[0].goal == "Refactor parser"


def test_store_applies_domain_specific_memory_ranking(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("backend:parser", "Prefer backend parser guard", confidence=0.6)
    store.append_learning("frontend:parser", "Prefer frontend parser debounce", confidence=0.95)

    backend_ranked = store.retrieve(topic="Refactor parser", limit=2, domain="backend")
    assert backend_ranked
    assert backend_ranked[0].topic == "backend:parser"


def test_store_readonly_mode_does_not_create_files(tmp_path: Path) -> None:
    path = tmp_path / "readonly_brain.jsonl"
    store = SecondBrainStore(path, create_if_missing=False)

    assert store.retrieve(topic="any", limit=5) == []
    assert store.list_run_artifacts(limit=5) == []
    assert not path.exists()


def test_store_contradictions_are_scoped_by_topic(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("backend:parser", "Use helper extraction", confidence=0.8)
    store.append_learning(
        "backend:parser",
        "Inline parsing logic",
        confidence=0.7,
        contradicts="Use helper extraction",
    )
    store.append_learning("frontend:parser", "Use helper extraction", confidence=0.75)

    frontend_entries = store.retrieve("Refactor parser", limit=5, domain="frontend")
    assert frontend_entries
    assert frontend_entries[0].topic == "frontend:parser"


def test_store_tie_break_keeps_single_contradiction_winner(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("backend:parser", "A", confidence=0.8, contradicts="B")
    store.append_learning("backend:parser", "B", confidence=0.8, contradicts="A")

    entries = store.retrieve("backend:parser", limit=5)
    assert len(entries) == 1


def test_store_skips_malformed_relation_shapes(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")
    store.run_artifacts_path.write_text(
        '{"goal":"bad","success_criteria":"x","planner_decisions":[],"change_summary":[],'
        '"verification_outcomes":[],"failure_classifications":[],"recovery_attempts":[],'
        '"reuse_notes":[],"learnings":[],"final_disposition":"completed","missing_artifacts":[],'
        '"lane":"balanced","relations":[["too_short"]]}\n',
        encoding="utf-8",
    )

    entries = store.list_run_artifacts(limit=5)
    assert entries == []


def test_store_supports_relevance_weight_hooks(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")
    store.append_learning("backend:parser", "Backend guard", confidence=0.4)
    store.append_learning("frontend:parser", "Frontend debounce", confidence=0.9)

    ranked = store.retrieve(
        topic="Refactor parser",
        limit=2,
        domain="backend",
        relevance_weights={"backend": 0.8},
    )
    assert ranked
    assert ranked[0].topic == "backend:parser"


def test_store_applies_scheduled_hygiene_and_rewrites_entries(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")
    store.append_learning("backend:parser", "Use helper extraction", confidence=0.5)
    store.append_learning("backend:parser", "Use helper extraction", confidence=0.8)
    store.append_learning(
        "backend:parser",
        "Inline parser",
        confidence=0.6,
        contradicts="Use helper extraction",
    )

    summary = store.apply_scheduled_hygiene()
    entries = store.retrieve("backend:parser", limit=10)

    assert summary["deduplicated_count"] >= 0
    assert summary["action_count"] >= 1
    assert len(entries) == 1
    assert entries[0].learning == "Use helper extraction"
