// Unit tests for `startCapture` that don't require a real browser. We
// monkey-patch the local `chromium.launchPersistentContext` so the
// browser-launch path is replaced with an instant throw; only the
// pre-launch logic (mkdirSync on profileDir) actually runs.

import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, after } from "node:test";
import assert from "node:assert/strict";

import { chromium } from "../src/playwright.mjs";
import { startCapture } from "../src/capture.mjs";

const ROOT = mkdtempSync(join(tmpdir(), "har-browse-startcap-test-"));
after(() => rmSync(ROOT, { recursive: true, force: true }));

/**
 * Replace chromium.launchPersistentContext for the duration of an awaited
 * call. Restores the original on return — even on throw — so other tests
 * see the real implementation.
 */
async function withFakeChromium(fake, fn) {
  const original = chromium.launchPersistentContext;
  chromium.launchPersistentContext = fake;
  try {
    return await fn();
  } finally {
    chromium.launchPersistentContext = original;
  }
}

const SENTINEL = "STARTCAP_TEST_SENTINEL";

test("startCapture creates profileDir recursively (parents missing)", async () => {
  // Nested path two levels below an existing tmp dir; intermediate dirs
  // don't exist. Non-recursive mkdir errors with ENOENT before chromium
  // is reached. Recursive mkdir creates parents — control flow reaches
  // our fake launch and throws the sentinel.
  const profileDir = join(ROOT, "missing-parent", "missing-child", "profile");
  assert.equal(existsSync(profileDir), false);

  let launched = false;
  await assert.rejects(
    () =>
      withFakeChromium(
        async (dir, _opts) => {
          launched = true;
          assert.equal(dir, profileDir);
          throw new Error(SENTINEL);
        },
        () => startCapture({ url: "http://127.0.0.1:1", profileDir, headless: true }),
      ),
    new RegExp(SENTINEL),
  );

  assert.equal(launched, true, "expected to reach chromium.launchPersistentContext");
  assert.equal(existsSync(profileDir), true, "profileDir not created");
});
