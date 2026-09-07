from pathlib import Path

from onyx.aleiva_core.second_brain.store import SecondBrainStore
from onyx.aleiva_core.trading_analysis import run_trading_analysis_pack
from onyx.aleiva_core.trading_analysis import TradingAnalysisRequest


def test_trading_analysis_pack_enforces_non_execution_safeguards(tmp_path: Path) -> None:
    store = SecondBrainStore(tmp_path / "brain.jsonl")
    store.append_learning(
        "trading:BTCUSD",
        "Watch macro event windows before directional bias.",
        confidence=0.7,
    )
    result = run_trading_analysis_pack(
        TradingAnalysisRequest(
            market="crypto",
            symbol="BTCUSD",
            timeframe="4h",
            thesis="bullish continuation after consolidation",
        ),
        second_brain_store=store,
    )

    assert result.status == "analysis_only"
    assert result.analysis
    assert result.risk_review
    assert any("no order placement" in safeguard for safeguard in result.non_execution_safeguards)
    assert result.explainability["execution_enabled"] is False
