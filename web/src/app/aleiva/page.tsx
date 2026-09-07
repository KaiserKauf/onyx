"use client";

import { useCallback, useMemo, useState } from "react";
import useSWR from "swr";
import * as SettingsLayouts from "@/layouts/settings-layouts";
import { Section } from "@/layouts/general-layouts";
import Text from "@/refresh-components/texts/Text";
import SimpleLoader from "@/refresh-components/loaders/SimpleLoader";
import { Button } from "@opal/components";
import { toast } from "@/hooks/useToast";
import { errorHandlingFetcher } from "@/lib/fetcher";
import { SWR_KEYS } from "@/lib/swr-keys";
import type {
  AleivaRunResponse,
  AleivaRunStatusResponse,
} from "@/app/aleiva/interfaces";
import { runAutopilotDry } from "@/app/aleiva/api";
import { OnboardingGuide } from "@/app/aleiva/components/OnboardingGuide";
import { PlatformControlPanel } from "@/app/aleiva/components/PlatformControlPanel";
import { QueueStatusCards } from "@/app/aleiva/components/QueueStatusCards";
import { RunGoalPanel } from "@/app/aleiva/components/RunGoalPanel";
import { ExplainabilityPanel } from "@/app/aleiva/components/ExplainabilityPanel";
import { LatestRunsPanel } from "@/app/aleiva/components/LatestRunsPanel";
import { MemoryHygienePanel } from "@/app/aleiva/components/MemoryHygienePanel";
import { VoiceControlPanel } from "@/app/aleiva/components/VoiceControlPanel";
import { TradingAnalysisPanel } from "@/app/aleiva/components/TradingAnalysisPanel";
import { KpiTrendsPanel } from "@/app/aleiva/components/KpiTrendsPanel";
import { ADMIN_ROUTES } from "@/lib/admin-routes";
import { SvgPlayCircle, SvgRefreshCw } from "@opal/icons";

const route = ADMIN_ROUTES.ALEIVA;

export default function AleivaDashboardPage() {
  const { data, error, isLoading, mutate } = useSWR<AleivaRunStatusResponse>(
    SWR_KEYS.aleivaRunStatus,
    errorHandlingFetcher,
    { revalidateOnFocus: false }
  );
  const [lastDryRun, setLastDryRun] = useState<AleivaRunResponse | null>(null);
  const [autopilotBusy, setAutopilotBusy] = useState(false);

  const refresh = useCallback(() => {
    void mutate();
  }, [mutate]);

  const handleDryRunComplete = useCallback(
    (result: AleivaRunResponse) => {
      setLastDryRun(result);
      refresh();
    },
    [refresh]
  );

  const handleAutopilotDry = useCallback(async () => {
    setAutopilotBusy(true);
    try {
      const result = await runAutopilotDry();
      toast.success(
        `Autopilot dry-run processed ${result.cycles_completed} cycle(s).`
      );
      refresh();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Autopilot dry-run failed");
    } finally {
      setAutopilotBusy(false);
    }
  }, [refresh]);

  const headerActions = useMemo(
    () => (
      <div className="flex flex-wrap gap-1">
        <Button
          variant="default"
          prominence="secondary"
          icon={SvgRefreshCw}
          onClick={refresh}
          data-testid="aleiva-refresh-status"
        >
          Refresh
        </Button>
        <Button
          variant="default"
          prominence="primary"
          icon={SvgPlayCircle}
          onClick={() => void handleAutopilotDry()}
          disabled={autopilotBusy}
          data-testid="aleiva-autopilot-dry"
        >
          {autopilotBusy ? "Processing..." : "Process queue (dry)"}
        </Button>
      </div>
    ),
    [autopilotBusy, handleAutopilotDry, refresh]
  );

  return (
    <SettingsLayouts.Root width="lg">
      <SettingsLayouts.Header
        icon={route.icon}
        title={route.title}
        description="Autonomous run status, explainability, and second-brain hygiene — local-first with guardrails."
        rightChildren={headerActions}
      />
      <SettingsLayouts.Body>
        <OnboardingGuide />
        <PlatformControlPanel />

        {isLoading ? (
          <div className="flex justify-center py-12">
            <SimpleLoader className="h-6 w-6" />
          </div>
        ) : error ? (
          <Section gap={0.5}>
            <Text mainUiBody text03>
              Failed to load Aleiva status. Ensure the backend is running and you
              are signed in.
            </Text>
            <Button
              variant="default"
              prominence="secondary"
              icon={SvgRefreshCw}
              onClick={refresh}
            >
              Try again
            </Button>
          </Section>
        ) : (
          <Section gap={1.5}>
            <QueueStatusCards queue={data?.queue} />
            <KpiTrendsPanel kpiTrends={data?.kpi_trends} />
            <RunGoalPanel onDryRunComplete={handleDryRunComplete} />
            <ExplainabilityPanel
              explainability={lastDryRun?.explainability ?? null}
              lane={lastDryRun?.lane ?? null}
              status={lastDryRun?.status ?? null}
            />
            <LatestRunsPanel runs={data?.latest_runs} />
            <MemoryHygienePanel
              summary={data?.memory_hygiene}
              onHygieneComplete={refresh}
            />
            <VoiceControlPanel onControlComplete={refresh} />
            <TradingAnalysisPanel />
          </Section>
        )}
      </SettingsLayouts.Body>
    </SettingsLayouts.Root>
  );
}
