"use client";

import { useCallback, useState } from "react";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { toast } from "@/hooks/useToast";
import { runDryCycle } from "@/app/aleiva/api";
import type {
  AleivaPolicyTier,
  AleivaRunResponse,
} from "@/app/aleiva/interfaces";
import {
  POLICY_TIER_OPTIONS,
  STARTER_GOALS,
} from "@/app/aleiva/constants";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import { SvgPlayCircle, SvgPlus } from "@opal/icons";

interface RunGoalPanelProps {
  onDryRunComplete: (result: AleivaRunResponse) => void;
}

export function RunGoalPanel({ onDryRunComplete }: RunGoalPanelProps) {
  const [goal, setGoal] = useState("");
  const [policyTier, setPolicyTier] = useState<AleivaPolicyTier>("normal");
  const [busy, setBusy] = useState(false);

  const handleDryRun = useCallback(async () => {
    const trimmed = goal.trim();
    if (!trimmed) {
      toast.error("Enter a goal before running a dry cycle.");
      return;
    }
    setBusy(true);
    try {
      const result = await runDryCycle(trimmed, policyTier);
      onDryRunComplete(result);
      toast.success(`Dry run completed in ${result.lane} lane.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Dry run failed");
    } finally {
      setBusy(false);
    }
  }, [goal, onDryRunComplete, policyTier]);

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-run-goal-panel">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex flex-col gap-0.25">
            <Text mainUiAction text05>
              Dry-run explainability
            </Text>
            <Text secondaryBody text03>
              Preview planned steps, guardrails, and priority scores without
              mutating your workspace.
            </Text>
          </div>
          <label className="flex flex-col gap-0.5">
            <Text figureSmallLabel text03>
              Goal
            </Text>
            <textarea
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              rows={3}
              placeholder="Describe what Aleiva should plan and verify..."
              className="w-full rounded-08 border border-border-02 bg-background-tint-00 px-1 py-0.75 text-main-ui-body text-text-05 outline-none focus:border-status-success-04"
              data-testid="aleiva-goal-input"
            />
          </label>
          <Section gap={0.5}>
            <Text figureSmallLabel text03>
              Policy tier
            </Text>
            <div className="flex flex-wrap gap-1">
              {POLICY_TIER_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  variant="default"
                  prominence={
                    policyTier === option.value ? "primary" : "secondary"
                  }
                  size="sm"
                  onClick={() => setPolicyTier(option.value)}
                  data-testid={`aleiva-policy-${option.value}`}
                >
                  {option.label}
                </Button>
              ))}
            </div>
            <Text secondaryBody text03>
              {
                POLICY_TIER_OPTIONS.find((option) => option.value === policyTier)
                  ?.description
              }
            </Text>
          </Section>
          <div className="flex flex-col gap-0.5 md:flex-row md:items-end md:gap-2">
            <Button
              variant="default"
              prominence="primary"
              icon={SvgPlayCircle}
              onClick={() => void handleDryRun()}
              disabled={busy}
              data-testid="aleiva-dry-run-button"
            >
              {busy ? "Running dry cycle..." : "Run dry cycle"}
            </Button>
          </div>
          <Section gap={0.5}>
            <Text figureSmallLabel text03>
              Starter goals
            </Text>
            <div className="flex flex-wrap gap-1">
              {STARTER_GOALS.map((starter) => (
                <Button
                  key={starter}
                  variant="default"
                  prominence="secondary"
                  size="sm"
                  icon={SvgPlus}
                  onClick={() => setGoal(starter)}
                  data-testid={`aleiva-starter-${starter.slice(0, 12)}`}
                >
                  {starter}
                </Button>
              ))}
            </div>
          </Section>
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
