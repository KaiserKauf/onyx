"use client";

import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import type { AleivaDryRunExplainability } from "@/app/aleiva/interfaces";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";

interface ExplainabilityPanelProps {
  explainability: AleivaDryRunExplainability | null;
  lane: string | null;
  status: string | null;
}

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

export function ExplainabilityPanel({
  explainability,
  lane,
  status,
}: ExplainabilityPanelProps) {
  if (!explainability) {
    return (
      <AleivaMatrixShell className="p-0.5">
        <Card variant="tertiary" className="bg-transparent">
          <Text mainUiBody text03>
            Run a dry cycle to see explainability: decisions, safety checks,
            guardrail events, and ROI priority scores.
          </Text>
        </Card>
      </AleivaMatrixShell>
    );
  }

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-explainability">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex flex-wrap items-center gap-2">
            <Text mainUiAction text05>
              Explainability report
            </Text>
            {status && (
              <span className="rounded-08 bg-status-success-01 px-1 py-0.25">
                <Text figureSmallLabel className="text-status-success-05">
                  {status}
                </Text>
              </span>
            )}
            {lane && (
              <span className="rounded-08 bg-background-tint-02 px-1 py-0.25">
                <Text figureSmallLabel text03>
                  Lane: {lane}
                </Text>
              </span>
            )}
          </div>
          <BulletList
            title="Decisions"
            items={explainability.decisions}
            testId="aleiva-explain-decisions"
          />
          <BulletList
            title="Safety checks"
            items={explainability.safety_checks}
            testId="aleiva-explain-safety"
          />
          <BulletList
            title="Guardrail events"
            items={explainability.guardrail_events}
            testId="aleiva-explain-guardrails"
          />
          <BulletList
            title="Priority scores"
            items={explainability.priority_scores}
            testId="aleiva-explain-priority"
          />
          <BulletList
            title="Memory hygiene"
            items={explainability.memory_hygiene_actions}
            testId="aleiva-explain-memory"
          />
          {explainability.planned_steps.length > 0 && (
            <Section gap={0.25}>
              <Text figureSmallLabel text03>
                Planned steps preview
              </Text>
              <div className="rounded-08 border border-border-02 bg-background-tint-00 p-1 font-mono text-secondary-body text-text-03">
                {explainability.planned_steps.slice(0, 8).map((step) => (
                  <div key={step}>{step}</div>
                ))}
                {explainability.planned_steps.length > 8 && (
                  <div>…and {explainability.planned_steps.length - 8} more</div>
                )}
              </div>
            </Section>
          )}
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
