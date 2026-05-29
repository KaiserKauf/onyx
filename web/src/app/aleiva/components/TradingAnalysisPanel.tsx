"use client";

import { useCallback, useState } from "react";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { toast } from "@/hooks/useToast";
import { runTradingAnalysis } from "@/app/aleiva/api";
import type { AleivaTradingAnalysisResponse } from "@/app/aleiva/interfaces";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import { SvgPlayCircle } from "@opal/icons";

function BulletList({
  title,
  items,
  testId,
}: {
  title: string;
  items: string[];
  testId: string;
}) {
  if (items.length === 0) return null;
  return (
    <Section gap={0.25} data-testid={testId}>
      <Text figureSmallLabel text03>
        {title}
      </Text>
      <ul className="flex flex-col gap-0.25 pl-1">
        {items.map((item) => (
          <li key={`${title}-${item}`}>
            <Text secondaryBody text03>
              {item}
            </Text>
          </li>
        ))}
      </ul>
    </Section>
  );
}

export function TradingAnalysisPanel() {
  const [market, setMarket] = useState("crypto");
  const [symbol, setSymbol] = useState("BTC-USD");
  const [timeframe, setTimeframe] = useState("4h");
  const [thesis, setThesis] = useState("");
  const [riskFocus, setRiskFocus] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AleivaTradingAnalysisResponse | null>(
    null
  );

  const handleAnalyze = useCallback(async () => {
    const trimmedThesis = thesis.trim();
    if (!trimmedThesis) {
      toast.error("Enter a thesis before running analysis.");
      return;
    }
    setBusy(true);
    try {
      const response = await runTradingAnalysis({
        market: market.trim(),
        symbol: symbol.trim(),
        timeframe: timeframe.trim(),
        thesis: trimmedThesis,
        risk_focus: riskFocus.trim() || null,
      });
      setResult(response);
      toast.success("Trading analysis complete (analysis-only mode).");
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Trading analysis failed"
      );
    } finally {
      setBusy(false);
    }
  }, [market, riskFocus, symbol, thesis, timeframe]);

  const inputClassName =
    "w-full rounded-08 border border-border-02 bg-background-tint-00 px-1 py-0.75 text-main-ui-body text-text-05 outline-none focus:border-status-success-04";

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-trading-analysis">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex flex-col gap-0.25">
            <Text mainUiAction text05>
              Trading analysis (non-execution)
            </Text>
            <Text secondaryBody text03>
              Structured thesis review and risk scenarios — no order placement
              path. Outputs are for human review only.
            </Text>
          </div>

          <div className="grid gap-0.75 md:grid-cols-3">
            <label className="flex flex-col gap-0.5">
              <Text figureSmallLabel text03>
                Market
              </Text>
              <input
                value={market}
                onChange={(event) => setMarket(event.target.value)}
                className={inputClassName}
                data-testid="aleiva-trading-market"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <Text figureSmallLabel text03>
                Symbol
              </Text>
              <input
                value={symbol}
                onChange={(event) => setSymbol(event.target.value)}
                className={inputClassName}
                data-testid="aleiva-trading-symbol"
              />
            </label>
            <label className="flex flex-col gap-0.5">
              <Text figureSmallLabel text03>
                Timeframe
              </Text>
              <input
                value={timeframe}
                onChange={(event) => setTimeframe(event.target.value)}
                className={inputClassName}
                data-testid="aleiva-trading-timeframe"
              />
            </label>
          </div>

          <label className="flex flex-col gap-0.5">
            <Text figureSmallLabel text03>
              Thesis
            </Text>
            <textarea
              value={thesis}
              onChange={(event) => setThesis(event.target.value)}
              rows={3}
              placeholder="Describe the setup and invalidation criteria..."
              className={inputClassName}
              data-testid="aleiva-trading-thesis"
            />
          </label>

          <label className="flex flex-col gap-0.5">
            <Text figureSmallLabel text03>
              Risk focus (optional)
            </Text>
            <input
              value={riskFocus}
              onChange={(event) => setRiskFocus(event.target.value)}
              placeholder="e.g. liquidity during macro events"
              className={inputClassName}
              data-testid="aleiva-trading-risk-focus"
            />
          </label>

          <Button
            variant="default"
            prominence="primary"
            icon={SvgPlayCircle}
            onClick={() => void handleAnalyze()}
            disabled={busy}
            data-testid="aleiva-trading-analyze"
          >
            {busy ? "Analyzing..." : "Run analysis"}
          </Button>

          {result ? (
            <Section gap={0.75} data-testid="aleiva-trading-results">
              <Text figureSmallLabel text03>
                Status: {result.status}
              </Text>
              <BulletList
                title="Analysis"
                items={result.analysis}
                testId="aleiva-trading-analysis-list"
              />
              <BulletList
                title="Risk review"
                items={result.risk_review}
                testId="aleiva-trading-risk-list"
              />
              <BulletList
                title="Non-execution safeguards"
                items={result.non_execution_safeguards}
                testId="aleiva-trading-safeguards-list"
              />
            </Section>
          ) : null}
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
