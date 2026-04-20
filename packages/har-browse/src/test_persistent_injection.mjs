#!/usr/bin/env node
/**
 * Verify the "Done Capturing" button survives page navigations.
 * Spawns a toy server, drives Playwright through 3 navigations,
 * clicks the button, and checks the HAR has api/conversation entries.
 */
import { spawn } from "node:child_process";
import { chromium } from "playwright";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { injectOverlay } from "./inject.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const harPath = "/tmp/test-persistent-injection.har";
const port = 8765;

// Start toy server
const server = spawn(
  "python3",
  ["-m", "http.server", String(port), "--directory", join(__dirname, "..", "toy_server")],
  { stdio: ["ignore", "pipe", "pipe"] },
);
await new Promise((r) => setTimeout(r, 1000));

try {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    recordHar: { path: harPath, mode: "full" },
  });
  const page = await context.newPage();

  await injectOverlay(page);

  // Initial load
  await page.goto(`http://127.0.0.1:${port}`, { waitUntil: "networkidle" });
  const btn1 = await page.locator("#capture-done").count();
  console.log("After initial load: " + btn1);

  // Navigate (simulates login redirect)
  await page.goto(`http://127.0.0.1:${port}/index.html`, { waitUntil: "networkidle" });
  const btn2 = await page.locator("#capture-done").count();
  console.log("After 2nd navigation: " + btn2);

  // Navigate again
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });
  const btn3 = await page.locator("#capture-done").count();
  console.log("After 3rd navigation: " + btn3);

  // Click and verify
  await page.click("#capture-done");
  const clicked = await page.evaluate(
    () => document.getElementById("capture-done")?.dataset.clicked,
  );
  console.log("clicked: " + clicked);

  // Verify waitForFunction works (what har_browse.mjs uses)
  await page.waitForFunction(
    () => document.getElementById("capture-done")?.dataset.clicked === "true",
    { timeout: 5000 },
  );
  console.log("waitForFunction resolved");

  await context.close();
  await browser.close();

  // Verify HAR was written with api/conversation
  const har = JSON.parse(readFileSync(harPath, "utf-8"));
  const apiEntries = har.log.entries.filter((e) =>
    e.request.url.includes("/api/conversation"),
  );
  console.log("HAR api/conversation entries: " + apiEntries.length);

  const pass =
    btn1 === 1 &&
    btn2 === 1 &&
    btn3 === 1 &&
    clicked === "true" &&
    apiEntries.length >= 1;
  console.log(pass ? "PASS" : "FAIL");
  if (!pass) process.exit(1);
} finally {
  server.kill();
}
