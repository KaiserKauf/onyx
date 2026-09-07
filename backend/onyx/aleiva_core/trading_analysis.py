from __future__ import annotations

from dataclasses import dataclass

from onyx.aleiva_core.second_brain.store import SecondBrainStore


@dataclass(frozen=True)
class TradingAnalysisRequest:
    market: str
    symbol: str
    timeframe: str
    thesis: str
    risk_focus: str | None = None


@dataclass(frozen=True)
class TradingAnalysisResult:
    status: str
    analysis: list[str]
    risk_review: list[str]
    non_execution_safeguards: list[str]
    explainability: dict[str, object]


def run_trading_analysis_pack(
    request: TradingAnalysisRequest,
    *,
    second_brain_store: SecondBrainStore | None,
) -> TradingAnalysisResult:
    context = []
    if second_brain_store is not None:
        context = [
            entry.learning
            for entry in second_brain_store.retrieve(
                topic=f"trading:{request.symbol}",
                limit=3,
                domain="trading",
                relevance_weights={"trading": 0.5, request.market.lower(): 0.2},
            )
        ]

    analysis = [
        f"Assess structure for {request.symbol} on {request.timeframe} timeframe.",
        f"Thesis to validate: {request.thesis}",
        "Review volatility, liquidity, and event-calendar exposure before any decision.",
    ]
    if context:
        analysis.extend(f"Prior learning: {learning}" for learning in context)

    risk_review = [
        "Scenario stress: invalidation threshold breached.",
        "Scenario stress: spread/liquidity degradation during volatility spikes.",
        "Scenario stress: correlated-asset shock and concentration risk.",
    ]
    if request.risk_focus:
        risk_review.append(f"Focused risk concern: {request.risk_focus}")

    safeguards = [
        "analysis-only mode enabled: no order placement path available",
        "execution commands are explicitly disallowed in this feature pack",
        "outputs are recommendations for human review only",
    ]

    return TradingAnalysisResult(
        status="analysis_only",
        analysis=analysis,
        risk_review=risk_review,
        non_execution_safeguards=safeguards,
        explainability={
            "domain": "trading_analysis",
            "context_items_used": len(context),
            "execution_enabled": False,
        },
    )
