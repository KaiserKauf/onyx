/**
 * Aleiva Matrix API client — routes through the frontend BFF (`/api/aleiva/...`).
 */

import type {
  AleivaAutopilotRunResponse,
  AleivaMemoryHygieneRunResponse,
  AleivaPolicyTier,
  AleivaRunResponse,
  AleivaTradingAnalysisRequest,
  AleivaTradingAnalysisResponse,
  AleivaVoiceControlRequest,
  AleivaVoiceControlResponse,
} from "@/app/aleiva/interfaces";
import { ALEIVA_API_BASE } from "@/app/aleiva/constants";

async function readError(res: Response, fallback: string): Promise<never> {
  let detail: string | undefined;
  try {
    const body = (await res.json()) as { detail?: string; error_code?: string };
    detail = body?.detail;
  } catch {
    // ignore parse errors
  }
  throw new Error(detail || `${fallback} (HTTP ${res.status})`);
}

export async function runDryCycle(
  goal: string,
  policyTier: AleivaPolicyTier = "normal"
): Promise<AleivaRunResponse> {
  const res = await fetch(`${ALEIVA_API_BASE}/runs/dry`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, policy_tier: policyTier }),
  });
  if (!res.ok) await readError(res, "Failed to run Aleiva dry cycle");
  return (await res.json()) as AleivaRunResponse;
}

export async function runAutopilotDry(
  maxIterations = 5
): Promise<AleivaAutopilotRunResponse> {
  const res = await fetch(`${ALEIVA_API_BASE}/autopilot/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dry_run: true, max_iterations: maxIterations }),
  });
  if (!res.ok) await readError(res, "Failed to run Aleiva autopilot");
  return (await res.json()) as AleivaAutopilotRunResponse;
}

export async function runMemoryHygiene(): Promise<AleivaMemoryHygieneRunResponse> {
  const res = await fetch(`${ALEIVA_API_BASE}/memory/hygiene`, {
    method: "POST",
  });
  if (!res.ok) await readError(res, "Failed to run memory hygiene");
  return (await res.json()) as AleivaMemoryHygieneRunResponse;
}

export async function sendVoiceControl(
  request: AleivaVoiceControlRequest
): Promise<AleivaVoiceControlResponse> {
  const res = await fetch(`${ALEIVA_API_BASE}/voice/control`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      intent: request.intent,
      goal: request.goal ?? null,
      task_id: request.task_id ?? null,
      policy_tier: request.policy_tier ?? "safe",
    }),
  });
  if (!res.ok) await readError(res, "Failed to send voice control intent");
  return (await res.json()) as AleivaVoiceControlResponse;
}

export async function runTradingAnalysis(
  request: AleivaTradingAnalysisRequest
): Promise<AleivaTradingAnalysisResponse> {
  const res = await fetch(`${ALEIVA_API_BASE}/trading/analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      market: request.market,
      symbol: request.symbol,
      timeframe: request.timeframe,
      thesis: request.thesis,
      risk_focus: request.risk_focus ?? null,
    }),
  });
  if (!res.ok) await readError(res, "Failed to run trading analysis");
  return (await res.json()) as AleivaTradingAnalysisResponse;
}
