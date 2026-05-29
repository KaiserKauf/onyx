"use client";

import { useCallback, useState } from "react";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { toast } from "@/hooks/useToast";
import { sendVoiceControl } from "@/app/aleiva/api";
import type {
  AleivaPolicyTier,
  AleivaVoiceControlIntent,
  AleivaVoiceControlResponse,
} from "@/app/aleiva/interfaces";
import { POLICY_TIER_OPTIONS } from "@/app/aleiva/constants";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import { SvgMic, SvgPauseCircle, SvgPlayCircle, SvgRefreshCw } from "@opal/icons";

const VOICE_INTENT_OPTIONS: {
  value: AleivaVoiceControlIntent;
  label: string;
  description: string;
}[] = [
  {
    value: "start-run",
    label: "Start run",
    description: "Enqueue an autonomous run from a spoken or typed goal.",
  },
  {
    value: "pause-run",
    label: "Pause run",
    description: "Pause a queued or running task by task ID.",
  },
  {
    value: "status",
    label: "Status",
    description: "Fetch current queue counts without mutating state.",
  },
  {
    value: "report",
    label: "Report",
    description: "Read-only summary of recent runs and memory hygiene.",
  },
];

interface VoiceControlPanelProps {
  onControlComplete: () => void;
}

export function VoiceControlPanel({ onControlComplete }: VoiceControlPanelProps) {
  const [intent, setIntent] = useState<AleivaVoiceControlIntent>("status");
  const [goal, setGoal] = useState("");
  const [taskId, setTaskId] = useState("");
  const [policyTier, setPolicyTier] = useState<AleivaPolicyTier>("safe");
  const [busy, setBusy] = useState(false);
  const [lastResponse, setLastResponse] =
    useState<AleivaVoiceControlResponse | null>(null);

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    try {
      const result = await sendVoiceControl({
        intent,
        goal: intent === "start-run" ? goal.trim() || null : null,
        task_id: intent === "pause-run" ? taskId.trim() || null : null,
        policy_tier: policyTier,
      });
      setLastResponse(result);
      if (result.status === "accepted") {
        toast.success(result.message);
        onControlComplete();
      } else {
        toast.error(result.message);
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Voice control failed");
    } finally {
      setBusy(false);
    }
  }, [goal, intent, onControlComplete, policyTier, taskId]);

  const selectedIntent = VOICE_INTENT_OPTIONS.find(
    (option) => option.value === intent
  );

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-voice-control">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex flex-col gap-0.25">
            <Text mainUiAction text05>
              Voice control intents
            </Text>
            <Text secondaryBody text03>
              Simulate voice-first commands via POST /aleiva/voice/control —
              guardrails apply to every intent.
            </Text>
          </div>

          <Section gap={0.5}>
            <Text figureSmallLabel text03>
              Intent
            </Text>
            <div className="flex flex-wrap gap-1">
              {VOICE_INTENT_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  variant="default"
                  prominence={intent === option.value ? "primary" : "secondary"}
                  size="sm"
                  icon={
                    option.value === "start-run"
                      ? SvgPlayCircle
                      : option.value === "pause-run"
                        ? SvgPauseCircle
                        : option.value === "status"
                          ? SvgRefreshCw
                          : SvgMic
                  }
                  onClick={() => setIntent(option.value)}
                  data-testid={`aleiva-voice-intent-${option.value}`}
                >
                  {option.label}
                </Button>
              ))}
            </div>
            <Text secondaryBody text03>
              {selectedIntent?.description}
            </Text>
          </Section>

          {intent === "start-run" ? (
            <>
              <label className="flex flex-col gap-0.5">
                <Text figureSmallLabel text03>
                  Goal
                </Text>
                <input
                  value={goal}
                  onChange={(event) => setGoal(event.target.value)}
                  placeholder="Describe the run to enqueue..."
                  className="w-full rounded-08 border border-border-02 bg-background-tint-00 px-1 py-0.75 text-main-ui-body text-text-05 outline-none focus:border-status-success-04"
                  data-testid="aleiva-voice-goal-input"
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
                      data-testid={`aleiva-voice-policy-${option.value}`}
                    >
                      {option.label}
                    </Button>
                  ))}
                </div>
              </Section>
            </>
          ) : null}

          {intent === "pause-run" ? (
            <label className="flex flex-col gap-0.5">
              <Text figureSmallLabel text03>
                Task ID
              </Text>
              <input
                value={taskId}
                onChange={(event) => setTaskId(event.target.value)}
                placeholder="Paste task ID to pause..."
                className="w-full rounded-08 border border-border-02 bg-background-tint-00 px-1 py-0.75 text-main-ui-body text-text-05 outline-none focus:border-status-success-04"
                data-testid="aleiva-voice-task-id-input"
              />
            </label>
          ) : null}

          <Button
            variant="default"
            prominence="primary"
            icon={SvgMic}
            onClick={() => void handleSubmit()}
            disabled={busy}
            data-testid="aleiva-voice-submit"
          >
            {busy ? "Sending intent..." : "Send voice intent"}
          </Button>

          {lastResponse ? (
            <Section gap={0.5} data-testid="aleiva-voice-response">
              <Text figureSmallLabel text03>
                Last response
              </Text>
              <Text secondaryBody text03>
                {lastResponse.status}: {lastResponse.message}
              </Text>
              <Text secondaryBody text03>
                Queue — queued {lastResponse.queue.queued}, running{" "}
                {lastResponse.queue.running}, paused {lastResponse.queue.paused}
              </Text>
              {lastResponse.enqueued_task_id ? (
                <Text secondaryBody text03>
                  Enqueued task: {lastResponse.enqueued_task_id}
                </Text>
              ) : null}
              {lastResponse.report ? (
                <Section gap={0.25} data-testid="aleiva-voice-report">
                  <Text figureSmallLabel text03>
                    Control-plane report
                  </Text>
                  {Array.isArray(lastResponse.report.recent_runs) &&
                  lastResponse.report.recent_runs.length > 0 ? (
                    <ul className="flex flex-col gap-0.25 pl-1">
                      {(
                        lastResponse.report.recent_runs as Array<{
                          goal?: string;
                          final_disposition?: string;
                        }>
                      ).map((run) => (
                        <li key={`${run.goal}-${run.final_disposition}`}>
                          <Text secondaryBody text03>
                            {run.goal} — {run.final_disposition}
                          </Text>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <Text secondaryBody text03>
                      No recent runs recorded yet.
                    </Text>
                  )}
                  {Array.isArray(lastResponse.report.memory_hygiene_actions) &&
                  lastResponse.report.memory_hygiene_actions.length > 0 ? (
                    <ul className="flex flex-col gap-0.25 pl-1">
                      {(
                        lastResponse.report.memory_hygiene_actions as string[]
                      ).map((action) => (
                        <li key={action}>
                          <Text secondaryBody text03>
                            {action}
                          </Text>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </Section>
              ) : null}
            </Section>
          ) : null}
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
