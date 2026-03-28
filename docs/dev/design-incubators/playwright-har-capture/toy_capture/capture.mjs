#!/usr/bin/env node
import { chromium } from "playwright";
import { parseArgs } from "node:util";
import { injectOverlay } from "./inject.mjs";

const { values } = parseArgs({
  options: {
    url: { type: "string", default: "http://127.0.0.1:8000" },
    har: { type: "string", default: "out.har" },
  },
});

const browser = await chromium.launch({
  headless: false,
  // Playwright defaults to SwiftShader (software GL) which breaks Wayland
  // fractional scaling on Crostini — text stretches, mouse events offset from
  // visuals. Removing it lets Chromium use hardware GL via Sommelier.
  ignoreDefaultArgs: ["--enable-unsafe-swiftshader"],
});
const context = await browser.newContext({
  recordHar: { path: values.har, mode: "full" },
  // Playwright defaults to a 1280x720 viewport override, which doesn't match
  // the physical window size on Crostini. This causes fixed-position elements
  // to render off-screen. `null` lets the browser use its actual window size.
  viewport: null,
});
const page = await context.newPage();

await injectOverlay(page);

await page.goto(values.url, { waitUntil: "networkidle", timeout: 0 });
console.error("Page loaded. Waiting for human to click 'Done Capturing'...");

// Wait for the human to click — no timeout
await page.waitForFunction(
  () => document.getElementById("capture-done")?.dataset.clicked === "true",
  { timeout: 0 },
);

await context.close();
await browser.close();

console.error(`HAR written to ${values.har}`);
