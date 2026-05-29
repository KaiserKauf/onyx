"use client";

import { useState } from "react";
import Card from "@/refresh-components/cards/Card";
import Text from "@/refresh-components/texts/Text";
import { Button } from "@opal/components";
import { Section } from "@/layouts/general-layouts";
import { toast } from "@/hooks/useToast";
import { runMemoryHygiene } from "@/app/aleiva/api";
import type { AleivaMemoryHygieneSummary } from "@/app/aleiva/interfaces";
import { AleivaMatrixShell } from "@/app/aleiva/components/AleivaMatrixShell";
import { SvgRefreshCw } from "@opal/icons";

interface MemoryHygienePanelProps {
  summary: AleivaMemoryHygieneSummary | undefined;
  onHygieneComplete: () => void;
}

export function MemoryHygienePanel({
  summary,
  onHygieneComplete,
}: MemoryHygienePanelProps) {
  const [busy, setBusy] = useState(false);

  const handleRunHygiene = async () => {
    setBusy(true);
    try {
      const result = await runMemoryHygiene();
      toast.success(
        `Hygiene complete: ${result.action_count} action(s), ${result.deduplicated_count} deduplicated.`
      );
      onHygieneComplete();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Memory hygiene failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AleivaMatrixShell className="p-0.5" data-testid="aleiva-memory-hygiene">
      <Card variant="borderless" className="bg-transparent">
        <Section gap={0.75}>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div className="flex flex-col gap-0.25">
              <Text mainUiAction text05>
                Memory hygiene
              </Text>
              <Text secondaryBody text03>
                Sampled {summary?.sampled_entries ?? 0} learnings ·{" "}
                {summary?.action_count ?? 0} suggested action(s)
              </Text>
            </div>
            <Button
              variant="default"
              prominence="secondary"
              size="sm"
              icon={SvgRefreshCw}
              onClick={() => void handleRunHygiene()}
              disabled={busy}
              data-testid="aleiva-run-hygiene"
            >
              {busy ? "Running..." : "Run hygiene"}
            </Button>
          </div>
          {summary?.actions && summary.actions.length > 0 ? (
            <ul className="flex flex-col gap-0.25 pl-1">
              {summary.actions.slice(0, 6).map((action) => (
                <li key={action}>
                  <Text secondaryBody text03>
                    {action}
                  </Text>
                </li>
              ))}
            </ul>
          ) : (
            <Text secondaryBody text03>
              No hygiene actions suggested for the current sample.
            </Text>
          )}
        </Section>
      </Card>
    </AleivaMatrixShell>
  );
}
