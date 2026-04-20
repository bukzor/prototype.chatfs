#!/usr/bin/env node
/**
 * End-to-end test: captureHar() against the real internet (example.com).
 *
 * Exercises the real-site code path — launchPersistentContext, waitUntil
 * 'commit', the DONE/CANCEL race — that test_persistent_injection.mjs
 * doesn't cover (it reimplements an older capture flow against a local
 * toy server).
 *
 * Requires network access. Uses a temp profile dir so nothing leaks into
 * the user's XDG cache.
 */
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { captureHar } from "./capture.mjs";

const profileDir = mkdtempSync(join(tmpdir(), "har-browse-e2e-"));
const harPath = join(profileDir, "out.har");

try {
  const { outcome } = await captureHar({
    url: "https://example.com",
    harPath,
    profileDir,
    headless: true,
    onPageReady: async (page) => {
      await page.click("#capture-done");
    },
  });
  console.log("outcome: " + outcome);

  const har = JSON.parse(readFileSync(harPath, "utf-8"));
  const exampleEntries = har.log.entries.filter((e) =>
    e.request.url.includes("example.com"),
  );
  console.log("HAR example.com entries: " + exampleEntries.length);

  const pass = outcome === "done" && exampleEntries.length >= 1;
  console.log(pass ? "PASS" : "FAIL");
  if (!pass) process.exit(1);
} finally {
  rmSync(profileDir, { recursive: true, force: true });
}
