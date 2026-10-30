import { defineConfig } from "@playwright/test";

/** End-to-end tests in the installed Chrome against the dev site; motion is reduced so floating cards hold still for clicks. */
export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/.results",
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    channel: "chrome",
    reducedMotion: "reduce",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000/en",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
