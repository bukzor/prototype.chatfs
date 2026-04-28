/**
 * Verify the "Done Capturing" button survives page navigations.
 * Spawns a toy server, drives Playwright through 3 navigations,
 * clicks the button, and checks the HAR has api/conversation entries.
 */
import { spawn } from "node:child_process";
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { injectOverlay } from "./inject.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const harPath = "/tmp/test-persistent-injection.har";
const port = 8765;

let server;

before(async () => {
  server = spawn(
    "python3",
    [
      "-m",
      "http.server",
      String(port),
      "--directory",
      join(__dirname, "..", "toy_server"),
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  for (let i = 0; i < 50; i++) {
    try {
      if ((await fetch(`http://127.0.0.1:${port}/`)).ok) return;
    } catch {
      // server not yet listening; retry
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("toy server failed to start");
});

after(() => {
  server?.kill();
});

test("Done Capturing button survives navigations", { timeout: 60000 }, async () => {
  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({
      recordHar: { path: harPath, mode: "full" },
    });
    try {
      const page = await context.newPage();

      await injectOverlay(page);

      await page.goto(`http://127.0.0.1:${port}`, { waitUntil: "networkidle" });
      assert.equal(await page.locator("#capture-done").count(), 1, "after initial load");

      await page.goto(`http://127.0.0.1:${port}/index.html`, {
        waitUntil: "networkidle",
      });
      assert.equal(await page.locator("#capture-done").count(), 1, "after 2nd navigation");

      await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });
      assert.equal(await page.locator("#capture-done").count(), 1, "after 3rd navigation");

      await page.click("#capture-done");
      const clicked = await page.evaluate(
        () => document.getElementById("capture-done")?.dataset.clicked,
      );
      assert.equal(clicked, "true");

      await page.waitForFunction(
        () => document.getElementById("capture-done")?.dataset.clicked === "true",
        { timeout: 5000 },
      );
    } finally {
      await context.close();
    }
  } finally {
    await browser.close();
  }

  const har = JSON.parse(readFileSync(harPath, "utf-8"));
  const apiEntries = har.log.entries.filter((e) =>
    e.request.url.includes("/api/conversation"),
  );
  assert.ok(apiEntries.length >= 1, `HAR has api/conversation entries (got ${apiEntries.length})`);
});
