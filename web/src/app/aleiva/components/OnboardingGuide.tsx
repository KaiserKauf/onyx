"use client";

import { useCallback, useEffect, useState } from "react";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import {
  ALEIVA_ONBOARDING_STEPS,
  ALEIVA_ONBOARDING_STORAGE_KEY,
} from "@/app/aleiva/constants";
import { SvgCheckCircle, SvgChevronRight, SvgX } from "@opal/icons";

export function OnboardingGuide() {
  const [visible, setVisible] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    try {
      const completed = window.localStorage.getItem(ALEIVA_ONBOARDING_STORAGE_KEY);
      setVisible(completed !== "true");
    } catch {
      setVisible(true);
    }
  }, []);

  const dismiss = useCallback(() => {
    try {
      window.localStorage.setItem(ALEIVA_ONBOARDING_STORAGE_KEY, "true");
    } catch {
      // ignore storage failures
    }
    setVisible(false);
  }, []);

  if (!visible) return null;

  const step = ALEIVA_ONBOARDING_STEPS[stepIndex];
  const isLast = stepIndex === ALEIVA_ONBOARDING_STEPS.length - 1;

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-onboarding">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex items-start justify-between gap-2">
            <div className="flex flex-col gap-0.25">
              <Text figureSmallLabel text03>
                Guided onboarding · Step {stepIndex + 1} of{" "}
                {ALEIVA_ONBOARDING_STEPS.length}
              </Text>
              <Text headingH3 text05>
                {step.title}
              </Text>
            </div>
            <Button
              icon={SvgX}
              variant="default"
              prominence="tertiary"
              size="sm"
              onClick={dismiss}
              data-testid="aleiva-onboarding-dismiss"
              aria-label="Dismiss onboarding"
            />
          </div>
          <Text mainUiBody text03>
            {step.body}
          </Text>
          <div className="rounded-08 border border-dashed border-status-success-03/30 bg-status-success-01/30 px-1 py-0.75">
            <Text secondaryBody text03>
              <span className="font-medium text-status-success-05">
                What happens next:{" "}
              </span>
              {step.preview}
            </Text>
          </div>
          <div className="flex items-center justify-between gap-2 pt-0.25">
            <div className="flex gap-0.5">
              {ALEIVA_ONBOARDING_STEPS.map((item, index) => (
                <span
                  key={item.id}
                  className={
                    index === stepIndex
                      ? "h-1 w-4 rounded-full bg-status-success-05"
                      : "h-1 w-2 rounded-full bg-background-tint-03"
                  }
                />
              ))}
            </div>
            <div className="flex gap-0.5">
              {stepIndex > 0 && (
                <Button
                  variant="default"
                  prominence="secondary"
                  size="sm"
                  onClick={() => setStepIndex((current) => current - 1)}
                >
                  Back
                </Button>
              )}
              {isLast ? (
                <Button
                  variant="default"
                  prominence="primary"
                  size="sm"
                  icon={SvgCheckCircle}
                  onClick={dismiss}
                  data-testid="aleiva-onboarding-finish"
                >
                  Start exploring
                </Button>
              ) : (
                <Button
                  variant="default"
                  prominence="primary"
                  size="sm"
                  icon={SvgChevronRight}
                  onClick={() => setStepIndex((current) => current + 1)}
                  data-testid="aleiva-onboarding-next"
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
