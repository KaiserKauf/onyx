"use client";

import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Section } from "@/layouts/general-layouts";
import type { AleivaRunArtifactSummary } from "@/app/aleiva/interfaces";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";

interface LatestRunsPanelProps {
  runs: AleivaRunArtifactSummary[] | undefined;
}

export function LatestRunsPanel({ runs }: LatestRunsPanelProps) {
  if (!runs || runs.length === 0) {
    return (
      <Section gap={0.75} data-testid="aleiva-latest-runs">
        <Text mainUiAction text05>
          Latest runs
        </Text>
        <AleivaMatrixShell className="p-0.5">
          <Card variant="tertiary" className="bg-transparent">
            <Text mainUiBody text03>
              No run artifacts yet. Complete a dry or live cycle to populate the
              second brain.
            </Text>
          </Card>
        </AleivaMatrixShell>
      </Section>
    );
  }

  return (
    <Section gap={0.75} data-testid="aleiva-latest-runs">
      <Text mainUiAction text05>
        Latest runs
      </Text>
      <div className="flex flex-col gap-1">
        {runs.map((run) => (
          <AleivaMatrixShell key={`${run.goal}-${run.lane}`} className="p-0.5">
            <Card variant="borderless" className="bg-transparent">
              <Section gap={0.5}>
                <div className="flex flex-wrap items-center justify-between gap-1">
                  <Text mainUiBody text05>
                    {run.goal}
                  </Text>
                  <Text figureSmallLabel text03>
                    {run.final_disposition} · {run.lane}
                  </Text>
                </div>
                {run.verification_outcomes.length > 0 && (
                  <Text secondaryBody text03>
                    Verification: {run.verification_outcomes.join("; ")}
                  </Text>
                )}
                {run.missing_artifacts.length > 0 && (
                  <Text secondaryBody className="text-status-error-05">
                    Missing artifacts: {run.missing_artifacts.join(", ")}
                  </Text>
                )}
              </Section>
            </Card>
          </AleivaMatrixShell>
        ))}
      </div>
    </Section>
  );
}
