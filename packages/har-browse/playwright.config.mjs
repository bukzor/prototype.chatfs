import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "*.spec.mjs",
  timeout: 60_000,
  fullyParallel: true,
  reporter: "list",
  use: {
    headless: true,
  },
});
