from __future__ import annotations

from collections.abc import Iterable

_RELATION_PREFIXES: tuple[str, ...] = (
    "depends_on",
    "changed_in",
    "fixed_by",
    "invalidated_by",
    "related_to",
)

GraphRelation = tuple[str, str, str]


def extract_relations(source: str, statements: Iterable[str]) -> list[GraphRelation]:
    relations: list[GraphRelation] = []
    for statement in statements:
        normalized = statement.strip()
        if not normalized:
            continue

        relation = _parse_relation_statement(source=source, statement=normalized)
        relations.append(relation)

    return relations


def _parse_relation_statement(source: str, statement: str) -> GraphRelation:
    for relation_prefix in _RELATION_PREFIXES:
        marker = f"{relation_prefix}:"
        if statement.startswith(marker):
            return (source, relation_prefix, statement.removeprefix(marker).strip())
    return (source, "related_to", statement)
