from pathlib import Path

from onyx.aleiva_core.second_brain.graph import extract_relations
from onyx.aleiva_core.second_brain.store import SecondBrainStore


def test_store_persists_and_reads_latest(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")

    store.append_learning("parser", "Prefer helper extraction", confidence=0.7)

    results = store.retrieve("parser", limit=5)
    assert len(results) == 1
    assert results[0].learning == "Prefer helper extraction"
    assert results[0].confidence == 0.7


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
