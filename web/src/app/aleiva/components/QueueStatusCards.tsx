"use client";

import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import type { AleivaQueueSummary } from "@/app/aleiva/interfaces";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";

interface QueueStatusCardsProps {
  queue: AleivaQueueSummary | undefined;
}

interface QueueMetric {
  label: string;
  value: number;
  accentClass: string;
}

function buildMetrics(queue: AleivaQueueSummary | undefined): QueueMetric[] {
  return [
    {
      label: "Queued",
      value: queue?.queued ?? 0,
      accentClass: "text-text-03",
    },
    {
      label: "Running",
      value: queue?.running ?? 0,
      accentClass: "text-status-info-05",
    },
    {
      label: "Completed",
      value: queue?.completed ?? 0,
      accentClass: "text-status-success-05",
    },
    {
      label: "Failed",
      value: queue?.failed ?? 0,
      accentClass: "text-status-error-05",
    },
    {
      label: "Paused",
      value: queue?.paused ?? 0,
      accentClass: "text-text-03",
    },
  ];
}

export function QueueStatusCards({ queue }: QueueStatusCardsProps) {
  const metrics = buildMetrics(queue);

  return (
    <Section gap={0.75} data-testid="aleiva-queue-status">
      <Text mainUiAction text05>
        Run queue
      </Text>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
        {metrics.map((metric) => (
          <AleivaMatrixShell key={metric.label} className="p-0.5">
            <Card variant="borderless" className="bg-transparent py-1">
              <Text figureSmallLabel text03>
                {metric.label}
              </Text>
              <Text headingH2 className={metric.accentClass}>
                {metric.value}
              </Text>
            </Card>
          </AleivaMatrixShell>
        ))}
      </div>
    </Section>
  );
}
