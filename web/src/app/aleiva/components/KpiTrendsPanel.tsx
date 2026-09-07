"use client";

import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import type { AleivaKpiTrendsSummary } from "@/app/aleiva/explainability-types";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";

interface KpiTrendsPanelProps {
  kpiTrends: AleivaKpiTrendsSummary | null | undefined;
}

interface KpiMetricProps {
  label: string;
  value: number;
  testId: string;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function trendLabel(trend: AleivaKpiTrendsSummary["trend"]): string {
  switch (trend) {
    case "improving":
      return "Improving";
    case "declining":
      return "Declining";
    default:
      return "Stable";
  }
}

function trendClassName(trend: AleivaKpiTrendsSummary["trend"]): string {
  switch (trend) {
    case "improving":
      return "text-status-success-05";
    case "declining":
      return "text-status-error-05";
    default:
      return "text-text-03";
  }
}

function KpiMetric({ label, value, testId }: KpiMetricProps) {
  return (
    <AleivaMatrixShell className="p-0.5">
      <Card variant="borderless" className="bg-transparent py-1">
        <Text figureSmallLabel text03>
          {label}
        </Text>
        <Text headingH2 data-testid={testId}>
          {formatPercent(value)}
        </Text>
      </Card>
    </AleivaMatrixShell>
  );
}

export function KpiTrendsPanel({ kpiTrends }: KpiTrendsPanelProps) {
  if (!kpiTrends) {
    return (
      <AleivaMatrixShell className="p-0.5" data-testid="aleiva-kpi-trends">
        <Card variant="tertiary" className="bg-transparent">
          <Text mainUiBody text03>
            Run at least one Aleiva cycle to populate balanced KPI trends (speed,
            quality, knowledge reuse).
          </Text>
        </Card>
      </AleivaMatrixShell>
    );
  }

  const { current, trend, points } = kpiTrends;

  return (
    <Section gap={0.75} data-testid="aleiva-kpi-trends">
      <div className="flex flex-wrap items-center gap-2">
        <Text mainUiAction text05>
          Balanced KPI trends
        </Text>
        <span className="rounded-08 bg-background-tint-02 px-1 py-0.25">
          <Text
            figureSmallLabel
            className={trendClassName(trend)}
            data-testid="aleiva-kpi-trend-direction"
          >
            {trendLabel(trend)}
          </Text>
        </span>
        <span className="rounded-08 bg-background-tint-02 px-1 py-0.25">
          <Text figureSmallLabel text03>
            Lane: {current.lane}
          </Text>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <KpiMetric
          label="Speed"
          value={current.speed}
          testId="aleiva-kpi-speed"
        />
        <KpiMetric
          label="Quality"
          value={current.quality}
          testId="aleiva-kpi-quality"
        />
        <KpiMetric
          label="Knowledge reuse"
          value={current.knowledge_reuse}
          testId="aleiva-kpi-knowledge"
        />
      </div>

      {points.length > 0 ? (
        <Section gap={0.25} data-testid="aleiva-kpi-history">
          <Text figureSmallLabel text03>
            Recent run KPI history
          </Text>
          <ul className="flex flex-col gap-0.25 pl-1">
            {points.map((point) => (
              <li key={`${point.run_index}-${point.goal}`}>
                <Text secondaryBody text03>
                  Run {point.run_index}: {point.goal} — speed{" "}
                  {formatPercent(point.speed)}, quality{" "}
                  {formatPercent(point.quality)}, reuse{" "}
                  {formatPercent(point.knowledge_reuse)} ({point.lane})
                </Text>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}
    </Section>
  );
}
