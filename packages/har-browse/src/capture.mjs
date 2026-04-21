import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { injectOverlay } from "./inject.mjs";
import { userAgent } from "./user-agent.mjs";

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
 *   hook called after navigation, before the termination race. Tests use
 *   this to auto-click the overlay; CLI callers leave it undefined.
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
    // Playwright defaults to a 1280x720 viewport override, which doesn't match
    // the physical window size on Crostini. This causes fixed-position elements
    // to render off-screen. `null` lets the browser use its actual window size.
    viewport: null,
    userAgent: await userAgent(),
    ignoreDefaultArgs: [
      // Playwright defaults to SwiftShader (software GL) which breaks Wayland
      // fractional scaling on Crostini — text stretches, mouse events offset
      // from visuals. Removing it lets Chromium use hardware GL via Sommelier.
      "--enable-unsafe-swiftshader",
      // Suppresses the yellow "Chrome is being controlled by automated test
      // software" infobar and a few other automation-mode UI tells (password
      // manager / translate suppression). Cosmetic; the automation is still
      // real and CDP-driven.
      "--enable-automation",
    ],
    args: [
      // Hides navigator.webdriver at the blink level. Empirically required
      // (in addition to the --enable-automation strip above) to clear
      // Cloudflare Turnstile on cold logins.
      "--disable-blink-features=AutomationControlled",
    ],
  });
  // Disable default timeouts on everything the context owns: page waits,
  // page.goto, and context.waitForEvent("close") — the human may take any
  // amount of time to complete login/capture.
  context.setDefaultTimeout(0);

  const page = context.pages()[0] ?? await context.newPage();

  await injectOverlay(page, { howto });

  await page.goto(url, { waitUntil: "commit" });

  if (onPageReady) await onPageReady(page);

  const DONE = "done";
  const CANCEL = "cancel";

  const outcome = await Promise.race([
    page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
    ).then(() => DONE).catch(() => CANCEL),
    context.waitForEvent("close").then(() => CANCEL),
  ]);

  if (outcome === CANCEL) return { outcome: "cancel" };

  await context.close();
  return { outcome: "done" };
}
