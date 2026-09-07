from __future__ import annotations

from typing import Protocol


class PlannerAgent(Protocol):
    def __call__(self, goal: str) -> list[str]:
        ...


class CoderAgent(Protocol):
    def __call__(self, plan: list[str], dry_run: bool) -> list[str]:
        ...


class VerifierAgent(Protocol):
    def __call__(self, execution_summary: list[str]) -> list[str]:
        ...


class CriticAgent(Protocol):
    def __call__(self, goal: str, verification: list[str]) -> list[str]:
        ...
