#!/usr/bin/env node
import { chromium } from "playwright";
import { parseArgs } from "node:util";
import { readFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { injectOverlay } from "./inject.mjs";

const { values, positionals } = parseArgs({
  options: {
    har: { type: "string", default: "out.har" },
    howto: { type: "string" },
    profile: { type: "string", default: "default_profile" },
  },
  allowPositionals: true,
});
const url = positionals[0] || "http://127.0.0.1:8000";

const howto = values.howto
  ? readFileSync(values.howto, "utf-8")
  : undefined;

const cacheHome = process.env.XDG_CACHE_HOME || join(homedir(), ".cache");
const profileDir = join(cacheHome, "har-browse", "profile", values.profile);
mkdirSync(profileDir, { recursive: true });

const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  recordHar: { path: values.har, mode: "full" },
  // Playwright defaults to a 1280x720 viewport override, which doesn't match
  // the physical window size on Crostini. This causes fixed-position elements
  // to render off-screen. `null` lets the browser use its actual window size.
  viewport: null,
  // Playwright defaults to SwiftShader (software GL) which breaks Wayland
  // fractional scaling on Crostini — text stretches, mouse events offset from
  // visuals. Removing it lets Chromium use hardware GL via Sommelier.
  ignoreDefaultArgs: ["--enable-unsafe-swiftshader"],
});
const page = context.pages()[0] ?? await context.newPage();

await injectOverlay(page, { howto });

page.setDefaultTimeout(0);
await page.goto(url, { waitUntil: "commit" });
console.error("Page loaded. Waiting for human to click 'Done Capturing' or close the window...");

const DONE = "done";
const CANCEL = "cancel";

const outcome = await Promise.race([
  page.waitForFunction(
    () => document.getElementById("capture-done")?.dataset.clicked === "true",
  ).then(() => DONE).catch(() => CANCEL),
  context.waitForEvent("close").then(() => CANCEL),
]);

if (outcome === CANCEL) {
  console.error("Cancelled by user.");
  process.exit(2);
}

await context.close();
console.error(`HAR written to ${values.har}`);
