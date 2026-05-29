import type { Route } from "next";
import type { AleivaPolicyTier } from "@/app/aleiva/interfaces";

export const ALEIVA_DASHBOARD_PATH = "/aleiva" as Route;

export const ALEIVA_ONBOARDING_STORAGE_KEY = "aleiva-matrix-onboarding-complete";

export const ALEIVA_API_BASE = "/api/aleiva";

export const POLICY_TIER_OPTIONS: {
  value: AleivaPolicyTier;
  label: string;
  description: string;
}[] = [
  {
    value: "safe",
    label: "Safe",
    description: "Strictest guardrails; dry-run recommended for first use.",
  },
  {
    value: "normal",
    label: "Normal",
    description: "Balanced lane selection with standard verification depth.",
  },
  {
    value: "experimental",
    label: "Experimental",
    description: "Higher throughput lane; extra review before live runs.",
  },
];

export interface AleivaOnboardingStep {
  id: string;
  title: string;
  body: string;
  preview: string;
}

export const ALEIVA_ONBOARDING_STEPS: AleivaOnboardingStep[] = [
  {
    id: "welcome",
    title: "Welcome to Aleiva Matrix",
    body: "This dashboard surfaces autonomous run status, explainability, and memory hygiene from your local Aleiva core.",
    preview: "You stay in control — start with dry runs before any live execution.",
  },
  {
    id: "status",
    title: "Monitor queue and runs",
    body: "The status panel shows queued, running, and completed tasks plus recent run artifacts from the second brain.",
    preview: "Refresh status anytime to sync with the backend store.",
  },
  {
    id: "explain",
    title: "Preview before execution",
    body: "Dry-run explainability shows planned steps, safety checks, guardrail events, and ROI priority scores.",
    preview: "Review decisions and policy controls before enabling live runs.",
  },
  {
    id: "memory",
    title: "Keep knowledge healthy",
    body: "Memory hygiene summarizes deduplication and contradiction guidance so learnings stay trustworthy.",
    preview: "Run hygiene from the dashboard when recall quality drifts.",
  },
  {
    id: "voice",
    title: "Voice-first control plane",
    body: "Simulate start, pause, status, and report intents via the voice control panel — every path stays guardrail-bound.",
    preview: "Use status and report intents for read-only queue visibility.",
  },
  {
    id: "trading",
    title: "Trading analysis (non-execution)",
    body: "Structured thesis review with risk scenarios and explicit non-execution safeguards — no order placement path.",
    preview: "Outputs are recommendations for human review only.",
  },
];

export const STARTER_GOALS: string[] = [
  "Refactor parser module with focused unit tests",
  "Add integration coverage for new API endpoints",
  "Document acceptance scenarios for dry-run validation",
];
