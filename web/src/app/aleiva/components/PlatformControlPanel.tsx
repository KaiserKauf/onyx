"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import { fetchPlatformGuide } from "@/app/aleiva/api";
import type {
  AleivaAgentLearningStatusResponse,
  AleivaPlatformGuideResponse,
  AleivaPlatformSummary,
} from "@/app/aleiva/interfaces";
import { ALEIVA_PLATFORM_STORAGE_KEY } from "@/app/aleiva/constants";
import { errorHandlingFetcher } from "@/lib/fetcher";
import { SWR_KEYS } from "@/lib/swr-keys";
import { SvgExternalLink, SvgShield } from "@opal/icons";

const RISK_LABEL: Record<AleivaPlatformSummary["risk_level"], string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk — paper/sandbox only",
};

function riskBadgeClass(risk: AleivaPlatformSummary["risk_level"]): string {
  if (risk === "high") return "text-status-error-05 bg-status-error-01";
  if (risk === "medium") return "text-status-warning-05 bg-status-warning-01";
  return "text-status-success-05 bg-status-success-01";
}

export function PlatformControlPanel() {
  const { data: platforms, error: platformsError } = useSWR<AleivaPlatformSummary[]>(
    SWR_KEYS.aleivaPlatforms,
    errorHandlingFetcher,
    { revalidateOnFocus: false }
  );
  const { data: learningStatus } = useSWR<AleivaAgentLearningStatusResponse>(
    SWR_KEYS.aleivaLearningStatus,
    errorHandlingFetcher,
    { revalidateOnFocus: false }
  );

  const [selectedPlatformId, setSelectedPlatformId] = useState<string | null>(null);
  const [guide, setGuide] = useState<AleivaPlatformGuideResponse | null>(null);
  const [guideLoading, setGuideLoading] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(ALEIVA_PLATFORM_STORAGE_KEY);
      if (stored) setSelectedPlatformId(stored);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    if (!platforms?.length) return;
    if (selectedPlatformId && platforms.some((p) => p.id === selectedPlatformId)) {
      return;
    }
    setSelectedPlatformId(platforms[0]?.id ?? null);
  }, [platforms, selectedPlatformId]);

  const loadGuide = useCallback(async (platformId: string) => {
    setGuideLoading(true);
    try {
      const nextGuide = await fetchPlatformGuide(platformId);
      setGuide(nextGuide);
    } catch {
      setGuide(null);
    } finally {
      setGuideLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!selectedPlatformId) return;
    void loadGuide(selectedPlatformId);
  }, [selectedPlatformId, loadGuide]);

  const handleSelectPlatform = useCallback((platformId: string) => {
    setSelectedPlatformId(platformId);
    try {
      window.localStorage.setItem(ALEIVA_PLATFORM_STORAGE_KEY, platformId);
    } catch {
      // ignore
    }
  }, []);

  const selectedPlatform = useMemo(
    () => platforms?.find((platform) => platform.id === selectedPlatformId) ?? null,
    [platforms, selectedPlatformId]
  );

  const platformLearning = useMemo(
    () =>
      learningStatus?.platforms.find(
        (entry) => entry.platform_id === selectedPlatformId
      ) ?? null,
    [learningStatus, selectedPlatformId]
  );

  if (platformsError) {
    return (
      <AleivaMatrixShell data-testid="aleiva-platform-control">
        <Text mainUiBody text03>
          Platform registry unavailable. Ensure the backend is running.
        </Text>
      </AleivaMatrixShell>
    );
  }

  if (!platforms) {
    return (
      <AleivaMatrixShell data-testid="aleiva-platform-control">
        <Text mainUiBody text03>
          Loading platform registry…
        </Text>
      </AleivaMatrixShell>
    );
  }

  return (
    <AleivaMatrixShell data-testid="aleiva-platform-control">
      <Section gap={1}>
        <div className="flex flex-col gap-0.25">
          <Text figureSmallLabel text03>
            Multi-domain control
          </Text>
          <Text mainUiBody>
            Switch between AleivaOS, Vulty, music, and quantum trading surfaces.
            Trading platforms stay paper/sandbox-first.
          </Text>
        </div>

        <div
          className="flex flex-wrap gap-0.5"
          role="tablist"
          aria-label="Aleiva platforms"
        >
          {platforms.map((platform) => (
            <Button
              key={platform.id}
              variant="default"
              prominence={
                platform.id === selectedPlatformId ? "primary" : "secondary"
              }
              onClick={() => handleSelectPlatform(platform.id)}
              data-testid={`aleiva-platform-tab-${platform.id}`}
            >
              {platform.display_name}
            </Button>
          ))}
        </div>

        {selectedPlatform ? (
          <Card variant="raised">
            <Section gap={0.75}>
              <div className="flex flex-wrap items-center gap-0.5">
                <Text figureSmallLabel>{selectedPlatform.display_name}</Text>
                <span
                  className={`rounded px-0.5 py-0.125 text-xs font-medium ${riskBadgeClass(selectedPlatform.risk_level)}`}
                  data-testid="aleiva-platform-risk-badge"
                >
                  {RISK_LABEL[selectedPlatform.risk_level]}
                </span>
              </div>

              <Text secondaryBody text03>
                Domains: {selectedPlatform.domains.join(", ")}
              </Text>

              {platformLearning ? (
                <Text secondaryBody text03 data-testid="aleiva-platform-learning-summary">
                  Learnings: {platformLearning.learning_count} · Runs:{" "}
                  {platformLearning.run_count}
                  {platformLearning.latest_snapshot_commit
                    ? ` · Snapshot ${platformLearning.latest_snapshot_commit.slice(0, 12)}`
                    : ""}
                </Text>
              ) : null}

              {guideLoading ? (
                <Text secondaryBody text03>
                  Loading guided onboarding…
                </Text>
              ) : guide ? (
                <Section gap={0.5} data-testid="aleiva-platform-guide">
                  <div className="flex items-center gap-0.25">
                    <SvgShield className="h-4 w-4" />
                    <Text figureSmallLabel>Guided onboarding</Text>
                  </div>
                  <ol className="list-decimal pl-1.25 space-y-0.25">
                    {guide.onboarding_steps.map((step) => (
                      <li key={step}>
                        <Text secondaryBody>{step}</Text>
                      </li>
                    ))}
                  </ol>
                  {guide.trading_mode === "paper_sandbox_only" ? (
                    <Text secondaryBody text03 data-testid="aleiva-trading-sandbox-copy">
                      Paper/sandbox mode only. Live execution requires explicit
                      human approval. Not financial advice.
                    </Text>
                  ) : null}
                  {guide.control_surface_url ? (
                    <Button
                      variant="default"
                      prominence="secondary"
                      icon={SvgExternalLink}
                      onClick={() =>
                        window.open(guide.control_surface_url ?? "", "_blank")
                      }
                      data-testid="aleiva-platform-open-control"
                    >
                      Open control surface
                    </Button>
                  ) : null}
                </Section>
              ) : null}
            </Section>
          </Card>
        ) : null}
      </Section>
    </AleivaMatrixShell>
  );
}
