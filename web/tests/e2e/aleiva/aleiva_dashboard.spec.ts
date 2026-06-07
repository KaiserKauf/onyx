import { test, expect } from "@playwright/test";

const ALEIVA_ONBOARDING_STORAGE_KEY = "aleiva-matrix-onboarding-complete";

test.describe("Aleiva Matrix dashboard", () => {
  test("loads dashboard and shows onboarding on first visit", async ({
    page,
  }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.removeItem(storageKey);
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.locator('[aria-label="admin-page-title"]')).toBeVisible();
    await expect(page.getByTestId("aleiva-onboarding")).toBeVisible();
    await expect(page.getByText("Welcome to Aleiva Matrix")).toBeVisible();
    await expect(page.getByTestId("aleiva-run-goal-panel")).toBeVisible();
  });

  test("dry-run flow shows explainability panel", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("aleiva-run-goal-panel")).toBeVisible();

    const goal = "Document acceptance scenarios for dry-run validation";
    await page.getByTestId("aleiva-goal-input").fill(goal);

    const dryRunResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/runs/dry") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-dry-run-button").click();
    await dryRunResponse;

    await expect(page.getByTestId("aleiva-explainability")).toBeVisible({
      timeout: 15000,
    });
    await expect(page.getByTestId("aleiva-explain-decisions")).toBeVisible();
    await expect(page.getByText("Explainability report")).toBeVisible();
  });

  test("voice control status intent returns queue summary", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("aleiva-voice-control")).toBeVisible();
    await page.getByTestId("aleiva-voice-intent-status").click();

    const voiceResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/voice/control") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-voice-submit").click();
    await voiceResponse;

    await expect(page.getByTestId("aleiva-voice-response")).toBeVisible();
    await expect(page.getByText(/Queue — queued/)).toBeVisible();
    await expect(page.getByText(/running/)).toBeVisible();
  });

  test("voice control start-run enqueues task with goal", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await page.getByTestId("aleiva-voice-intent-start-run").click();
    await page
      .getByTestId("aleiva-voice-goal-input")
      .fill("Voice-enqueued Aleiva smoke goal");

    const voiceResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/voice/control") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-voice-submit").click();
    const response = await voiceResponse;
    const body = (await response.json()) as {
      status: string;
      enqueued_task_id: string | null;
    };

    await expect(page.getByTestId("aleiva-voice-response")).toBeVisible();
    expect(body.status).toBe("accepted");
    expect(body.enqueued_task_id).toBeTruthy();
    await expect(page.getByText(/Enqueued task:/)).toBeVisible();
  });

  test("voice control report intent shows control-plane report", async ({
    page,
  }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await page.getByTestId("aleiva-voice-intent-report").click();

    const voiceResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/voice/control") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-voice-submit").click();
    await voiceResponse;

    await expect(page.getByTestId("aleiva-voice-report")).toBeVisible();
  });

  test("trading analysis panel submits thesis and shows safeguards", async ({
    page,
  }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("aleiva-trading-analysis")).toBeVisible();
    await page
      .getByTestId("aleiva-trading-thesis")
      .fill("Bullish continuation after consolidation with clear invalidation");

    const analysisResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/trading/analysis") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-trading-analyze").click();
    await analysisResponse;

    await expect(page.getByTestId("aleiva-trading-results")).toBeVisible();
    await expect(page.getByTestId("aleiva-trading-safeguards-list")).toBeVisible();
    await expect(page.getByTestId("aleiva-trading-analysis-list")).toBeVisible();
    await expect(page.getByTestId("aleiva-trading-risk-list")).toBeVisible();
    await expect(page.getByText("analysis_only")).toBeVisible();
    await expect(
      page.getByText(/analysis-only mode enabled/i)
    ).toBeVisible();
  });

  test("memory hygiene panel runs hygiene endpoint", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("aleiva-memory-hygiene")).toBeVisible();

    const hygieneResponse = page.waitForResponse(
      (response) =>
        response.url().includes("/api/aleiva/memory/hygiene") &&
        response.status() === 200
    );
    await page.getByTestId("aleiva-run-hygiene").click();
    await hygieneResponse;

    await expect(page.getByText(/Hygiene complete:/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("kpi trends panel renders after status load", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/aleiva");
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("aleiva-kpi-trends")).toBeVisible();
    await expect(page.getByText("Balanced KPI trends")).toBeVisible();
  });

  test("admin sidebar links to Aleiva dashboard", async ({ page }) => {
    await page.addInitScript((storageKey) => {
      window.localStorage.setItem(storageKey, "true");
    }, ALEIVA_ONBOARDING_STORAGE_KEY);

    await page.goto("/admin/configuration/language-models");
    await page.waitForLoadState("networkidle");

    await page.getByRole("link", { name: "Aleiva Matrix" }).click();
    await expect(page).toHaveURL("/aleiva");
    await expect(page.locator('[aria-label="admin-page-title"]')).toBeVisible();
  });
});
