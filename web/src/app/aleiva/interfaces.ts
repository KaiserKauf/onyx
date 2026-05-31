import type {
  AleivaDryRunExplainability,
  AleivaKpiTrendsSummary,
} from "@/app/aleiva/explainability-types";

export type {
  AleivaDryRunExplainability,
  AleivaExplainabilityEnvelope,
  AleivaKpiSnapshot,
  AleivaKpiTrendDirection,
  AleivaKpiTrendPoint,
  AleivaKpiTrendsSummary,
  AleivaMemoryHygieneActionDetail,
  AleivaPriorityScoreDetail,
} from "@/app/aleiva/explainability-types";

export type AleivaPolicyTier = "safe" | "normal" | "experimental";

export interface AleivaQueueSummary {
  queued: number;
  running: number;
  completed: number;
  failed: number;
  paused: number;
}

export interface AleivaRunArtifactSummary {
  goal: string;
  final_disposition: string;
  lane: string;
  missing_artifacts: string[];
  verification_outcomes: string[];
}

export interface AleivaMemoryHygieneSummary {
  sampled_entries: number;
  action_count: number;
  actions: string[];
}

export interface AleivaRunStatusResponse {
  queue: AleivaQueueSummary;
  latest_runs: AleivaRunArtifactSummary[];
  memory_hygiene: AleivaMemoryHygieneSummary;
  kpi_trends: AleivaKpiTrendsSummary | null;
}

export interface AleivaRunResponse {
  status: string;
  lane: string;
  plan: string[];
  execution: string[];
  verification: string[];
  learnings: string[];
  policy_tier: string | null;
  policy_controls: Record<string, number | string> | null;
  guardrail_events: string[] | null;
  explainability: AleivaDryRunExplainability | null;
}

export interface AleivaAutopilotCycleSummary {
  task_id: string;
  goal: string;
  status: string;
  reason: string;
  run_status: string | null;
}

export interface AleivaAutopilotRunResponse {
  cycles_completed: number;
  cycles: AleivaAutopilotCycleSummary[];
  queue: AleivaQueueSummary;
}

export interface AleivaMemoryHygieneRunResponse {
  deduplicated_count: number;
  decay_action_count: number;
  action_count: number;
  contradiction_guidance: string[];
  actions: string[];
}

export type AleivaVoiceControlIntent =
  | "start-run"
  | "pause-run"
  | "status"
  | "report";

export interface AleivaVoiceControlRequest {
  intent: AleivaVoiceControlIntent;
  goal?: string | null;
  task_id?: string | null;
  policy_tier?: AleivaPolicyTier;
}

export interface AleivaVoiceControlResponse {
  status: string;
  message: string;
  queue: AleivaQueueSummary;
  enqueued_task_id: string | null;
  report: Record<string, unknown> | null;
}

export interface AleivaTradingAnalysisRequest {
  market: string;
  symbol: string;
  timeframe: string;
  thesis: string;
  risk_focus?: string | null;
}

export interface AleivaTradingAnalysisResponse {
  status: string;
  analysis: string[];
  risk_review: string[];
  non_execution_safeguards: string[];
  explainability: Record<string, unknown>;
}
