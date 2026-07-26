// @ts-check
// puppeteer-core host shell behind `capture.mjs`'s CaptureHost seam --
// the production capture path (ratified 2026-07-23,
// todo.kb/2026-07-23-002-*). Playwright remains a devDependency for
// the test suite; its shell is `host_playwright.mjs`.
import { mkdirSync } from "node:fs";
import puppeteer from "puppeteer-core";
import { overlayInitScript } from "./inject.mjs";
import { captureStream } from "./capture.mjs";
import pkg from "../package.json" with { type: "json" };

/** @typedef {import("./capture.mjs").CDPEvent} CDPEvent */
/** @typedef {import("./capture.mjs").HostSession} HostSession */
/** @typedef {import("puppeteer-core").Page} Page */
/** @typedef {import("puppeteer-core").Browser} Browser */

// Self-identifying User-Agent suffix, following the standard
// `ToolName/Version (+ContactURL)` convention, so operators can
// identify this tool's traffic and reach the maintainer.
const UA_SUFFIX = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;

/**
 * Locate a Chromium for puppeteer-core (which bundles no browser).
 * `$HAR_BROWSE_BROWSER` wins; otherwise use Playwright's installed
 * Chromium -- already pinned by the devDependency, so captures and the
 * test suite share one browser revision (fingerprint stability per
 * `unblocked-sessions`). Dynamic import: playwright is a dev-only
 * dependency, and the production module graph stays free of it.
 */
async function executablePath() {
  if (process.env.HAR_BROWSE_BROWSER) return process.env.HAR_BROWSE_BROWSER;
  const { chromium } = await import("playwright-core");
  return chromium.executablePath();
}

/**
 * Adapt one puppeteer page to a `HostSession`: raw send plus blanket
 * event subscription, with the branded UA applied before any capture
 * domain is enabled.
 *
 * @param {Page} page
 * @param {string} brandedUA
 * @returns {Promise<HostSession>}
 */
async function hostSession(page, brandedUA) {
  const cdp = await page.createCDPSession();
  await cdp.send("Network.setUserAgentOverride", { userAgent: brandedUA });
  return {
    send: (method, params) =>
      cdp.send(/** @type {any} */ (method), /** @type {any} */ (params)),
    onEvent: (cb) => {
      // puppeteer's EventEmitter is mitt-style: '*' receives every
      // event as (type, payload). Protocol events are the dotted names;
      // the rest are puppeteer-internal (e.g. session lifecycle).
      // The declared '*' handler type takes the payload only, but the
      // mitt-backed emitter actually calls wildcard handlers with
      // (type, payload) -- hence the cast.
      cdp.on(
        "*",
        /** @type {any} */ (
          /** @param {unknown} name @param {any} params */
          (name, params) => {
            if (typeof name === "string" && name.includes(".")) {
              cb(name, params ?? {});
            }
          }
        ),
      );
    },
  };
}

/**
 * Wire capture onto an existing puppeteer page. Stream ends on
 * injected "Done" click or browser disconnect. Caller owns the browser
 * lifecycle.
 *
 * @param {Page} page
 * @param {{ howto?: string, drainGraceMs?: number }} [opts]
 * @returns {Promise<{
 *   events: AsyncIterable<CDPEvent>,
 *   done: Promise<void>,
 * }>}
 */
export async function attachCapture(page, { howto, drainGraceMs } = {}) {
  const browser = page.browser();
  const brandedUA = `${await browser.userAgent()} ${UA_SUFFIX}`;

  /** @type {() => void} */
  let resolveCut = () => {};
  /** @type {Promise<void>} */
  const cut = new Promise((res) => {
    resolveCut = res;
  });

  const { events, done } = await captureStream(
    {
      initialTarget: page,
      onTarget: (cb) => {
        browser.on("targetcreated", async (t) => {
          if (t.type() !== "page") return;
          const p = await t.page();
          if (p) cb(p);
        });
      },
      session: (target) => hostSession(/** @type {Page} */ (target), brandedUA),
      cut,
    },
    { drainGraceMs },
  );

  const { fn, arg } = overlayInitScript({ howto });
  await page.evaluateOnNewDocument(fn, arg);

  Promise.race([
    page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
      { polling: "raf", timeout: 0 },
    ),
    new Promise((res) => browser.once("disconnected", res)),
  ])
    .catch(() => {})
    .then(resolveCut);

  return { events, done };
}

/**
 * Launch a persistent-profile browser, navigate, and return a capture
 * session. Per-profile state persists under `profileDir`.
 *
 * `clearOriginStorage` defaults off here and on in the `har-browse`
 * CLI. The asymmetry is deliberate: this is the primitive, and it does
 * only what it is asked; the CLI is the capture *flow*, where a
 * silently payload-free capture is the worse failure.
 *
 * @param {{
 *   url: string,
 *   profileDir: string,
 *   howto?: string,
 *   headless?: boolean,
 *   drainGraceMs?: number,
 *   clearOriginStorage?: boolean,
 * }} opts
 * @returns {Promise<{
 *   page: Page,
 *   browser: Browser,
 *   events: AsyncIterable<CDPEvent>,
 *   done: Promise<void>,
 *   close: () => Promise<void>,
 * }>}
 */
export async function startCapture({
  url,
  profileDir,
  howto,
  headless = false,
  drainGraceMs,
  clearOriginStorage = false,
}) {
  mkdirSync(profileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: await executablePath(),
    userDataDir: profileDir,
    headless,
    // Use the real window size: a fixed viewport override pushes
    // fixed-position elements off-screen on Crostini's smaller windows.
    defaultViewport: null,
    // No "controlled by automated software" infobar or automation-mode
    // UI tells; the capture itself is CDP-driven and unaffected.
    ignoreDefaultArgs: ["--enable-automation"],
    args: [
      // Hides navigator.webdriver at the blink level. Empirically
      // required (in addition to --enable-automation stripping) to
      // clear Cloudflare Turnstile on cold logins.
      "--disable-blink-features=AutomationControlled",
      // A reused profile can offer to restore the previous session's
      // tabs; a capture run always starts from its own navigation.
      "--hide-crash-restore-bubble",
    ],
  });
  // Human may take any amount of time to complete login/capture.
  const pages = await browser.pages();
  const page = pages[0] ?? (await browser.newPage());
  page.setDefaultTimeout(0);

  const { events, done } = await attachCapture(page, { howto, drainGraceMs });
  if (clearOriginStorage) {
    // Wipe the target origin's app-level data caches BEFORE navigation,
    // so an app that persisted them (claude.ai's React Query cache in
    // IndexedDB; a service worker's cache-first store) must
    // re-materialize its data as capturable network traffic. Origin
    // comes from the target `url` — the page still sits on about:blank
    // here. Cookies are untouched: login state is why the profile
    // persists at all. `local_storage` stays out for the same reason
    // (some providers keep auth tokens there).
    const session = await page.createCDPSession();
    await session.send("Storage.clearDataForOrigin", {
      origin: new URL(url).origin,
      storageTypes: "indexeddb,cache_storage",
    });
    await session.detach();
  }
  // Navigate with commit semantics -- return as soon as the navigation
  // starts, so any site works (SPAs holding SSE/websockets never reach
  // a load-ish lifecycle state; puppeteer's goto has no "commit").
  const nav = await page.createCDPSession();
  await nav.send("Page.navigate", { url });
  await nav.detach();

  const close = async () => {
    await browser.close().catch(() => {});
    await done;
  };

  return { page, browser, events, done, close };
}
