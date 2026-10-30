import { defineConfig } from "@playwright/test";

/** E2E_BASE_URL points the tests at a running site (e.g. the local production stack, https://localhost). */
const target = process.env.E2E_BASE_URL;

/** End-to-end tests in the installed Chrome against the dev site; motion is reduced so floating cards hold still for clicks. */
export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/.results",
  reporter: "list",
  use: {
    baseURL: target ?? "http://localhost:3000",
    ignoreHTTPSErrors: !!target,
    channel: "chrome",
    reducedMotion: "reduce",
  },
  webServer: target
    ? undefined
    : {
        command: "npm run dev",
        url: "http://localhost:3000/en",
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
