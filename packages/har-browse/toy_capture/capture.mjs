#!/usr/bin/env node
import { chromium } from "playwright";
import { parseArgs } from "node:util";
import { readFileSync } from "node:fs";
import { injectOverlay } from "./inject.mjs";

const { values, positionals } = parseArgs({
  options: {
    har: { type: "string", default: "out.har" },
    howto: { type: "string" },
  },
  allowPositionals: true,
});
const url = positionals[0] || "http://127.0.0.1:8000";

const howto = values.howto
  ? readFileSync(values.howto, "utf-8")
  : undefined;

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

await injectOverlay(page, { howto });

page.setDefaultTimeout(0);
await page.goto(url, { waitUntil: "networkidle" });
console.error("Page loaded. Waiting for human to click 'Done Capturing'...");

// Wait for the human to click — no timeout
try {
  await page.waitForFunction(
    () => document.getElementById("capture-done")?.dataset.clicked === "true",
  );
} catch (e) {
  if (e.message.includes("has been closed")) {
    console.error("Cancelled by user.");
    process.exit(0);
  }
  throw e;
}

await context.close();
await browser.close();

console.error(`HAR written to ${values.har}`);
