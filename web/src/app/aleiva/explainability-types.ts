/**
 * Shared Aleiva explainability types used by dry-run responses and domain packs.
 * Keep in sync with `backend/onyx/server/features/aleiva/models.py`.
 */

export interface AleivaPriorityScoreDetail {
  task: string;
  impact: number;
  confidence: number;
  effort: number;
  score: number;
}

export interface AleivaMemoryHygieneActionDetail {
  action_type: string;
  message: string;
  topic: string;
  learning: string;
  contradicted_learning: string | null;
  previous_confidence: number | null;
  updated_confidence: number | null;
}

export interface AleivaDryRunExplainability {
  goal: string;
  policy_tier: string;
  decisions: string[];
  planned_steps: string[];
  safety_checks: string[];
  priority_scores: string[];
  memory_hygiene_actions: string[];
  guardrail_events: string[];
  policy_controls: Record<string, number | string>;
  priority_score_details: AleivaPriorityScoreDetail[];
  memory_hygiene_action_details: AleivaMemoryHygieneActionDetail[];
}

export interface AleivaExplainabilityEnvelope {
  explainability: AleivaDryRunExplainability | Record<string, unknown> | null;
}

export type AleivaKpiTrendDirection = "improving" | "stable" | "declining";

export interface AleivaKpiSnapshot {
  speed: number;
  quality: number;
  knowledge_reuse: number;
  lane: string;
}

export interface AleivaKpiTrendPoint {
  run_index: number;
  goal: string;
  speed: number;
  quality: number;
  knowledge_reuse: number;
  lane: string;
}

export interface AleivaKpiTrendsSummary {
  current: AleivaKpiSnapshot;
  trend: AleivaKpiTrendDirection;
  points: AleivaKpiTrendPoint[];
}
