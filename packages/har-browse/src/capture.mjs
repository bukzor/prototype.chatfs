import { mkdirSync } from "node:fs";
import { chromium } from "./playwright.mjs";
import { injectOverlay } from "./inject.mjs";

/**
 * Launch a persistent-context browser, record HAR, wait for termination.
 * Returns { outcome: "done" | "cancel" }.
 *
 * @param {object} opts
 * @param {string} opts.url
 * @param {string} opts.harPath
 * @param {string} opts.profileDir
 * @param {string} [opts.howto]  pre-read howto content (string, not path)
 * @param {boolean} [opts.headless=false]
 * @param {(page: import("playwright").Page) => Promise<void>} [opts.onPageReady]
 *   hook called after navigation, before the termination race.
 */
export async function captureHar({
  url,
  harPath,
  profileDir,
  howto,
  headless = false,
  onPageReady,
}) {
  mkdirSync(profileDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless,
    recordHar: { path: harPath, mode: "full" },
  });
  // Disable default timeouts on everything the context owns: page waits,
  // page.goto, and context.waitForEvent("close") — the human may take any
  // amount of time to complete login/capture.
  context.setDefaultTimeout(0);

  const page = context.pages()[0] ?? (await context.newPage());

  await injectOverlay(page, { howto });

  await page.goto(url, { waitUntil: "commit" });

  if (onPageReady) await onPageReady(page);

  const DONE = "done";
  const CANCEL = "cancel";

  const outcome = await Promise.race([
    page
      .waitForFunction(
        () =>
          document.getElementById("capture-done")?.dataset.clicked === "true",
      )
      .then(() => DONE)
      .catch(() => CANCEL),
    context.waitForEvent("close").then(() => CANCEL),
  ]);

  if (outcome === CANCEL) return { outcome: "cancel" };

  await context.close();
  return { outcome: "done" };
}
