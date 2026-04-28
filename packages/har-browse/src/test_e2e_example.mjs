/**
 * End-to-end test: captureEvents() against the real internet (example.com).
 *
 * Exercises the real-site code path — launchPersistentContext, waitUntil
 * 'commit', the streaming generator, the click-driven termination — that
 * test_persistent_injection.mjs doesn't cover.
 *
 * Requires network access. Uses a temp profile dir so nothing leaks into
 * the user's XDG cache.
 */
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { after, before, test } from "node:test";
import assert from "node:assert/strict";
import { captureEvents } from "./capture.mjs";

let profileDir;

before(() => {
  profileDir = mkdtempSync(join(tmpdir(), "har-browse-e2e-"));
});

after(() => {
  rmSync(profileDir, { recursive: true, force: true });
});

test("captureEvents against example.com", { timeout: 60000 }, async () => {
  const messages = [];
  for await (const msg of captureEvents({
    url: "https://example.com",
    profileDir,
    headless: true,
    onPageReady: async (page) => {
      // Wait for the page-level fetch to complete before signalling done,
      // so the responseReceived event for example.com has time to flush
      // with its body attached.
      await page.waitForLoadState("networkidle");
      await page.click("#capture-done");
    },
  })) {
    messages.push(msg);
  }

  const responses = messages.filter(
    (m) =>
      m.method === "Network.responseReceived" &&
      m.params.response?.url?.includes("example.com"),
  );
  assert.ok(responses.length >= 1, `got ${responses.length} example.com responses`);

  const r = responses[0];
  const body = r?.params?.response?.body ?? "";
  const text =
    r?.params?.response?.encoding === "base64"
      ? Buffer.from(body, "base64").toString("utf-8")
      : body;
  assert.match(text, /Example Domain/);
});
