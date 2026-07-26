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

// Self-identification: who we are and where to reach the maintainer,
// so operators can recognize this tool's traffic. Two spellings,
// because a User-Agent's two positions accept different grammars
// (RFC 9110 §10.1.5): inside a `comment` the text is free-form ctext,
// conventionally `; `-separated; as a `product` the name and version
// must be `token`s, and `;` and `:` are not token characters -- so the
// contact URL needs a comment of its own out there.
const UA_COMMENT_FIELDS = `${pkg.name}/${pkg.version}; +${pkg.homepage}`;
const UA_PRODUCT = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;

/**
 * Brand a User-Agent inside its platform comment, rather than as the
 * trailing `ToolName/Version (+ContactURL)` product the convention
 * would suggest.
 *
 * The convention is unusable against at least one major provider.
 * Measured 2026-07-26 (`design.kb/040-design.kb/self-identification.kb/`): Google denies
 * aistudio's GenerateContent outright -- `PERMISSION_DENIED`, while
 * every other RPC on the same service succeeds -- whenever anything
 * trails `Safari/537.36`. A neutral `Foo/1.0` is refused exactly like
 * our own name, so the gate is on the UA's *shape*, not on us; the same
 * identity in the platform comment is accepted, contact URL and all.
 *
 * This keeps `unblocked-sessions`' two halves compatible: we identify
 * honestly, and we still parse as the browser we actually are. The
 * client-hint metadata is unaffected -- `Sec-CH-UA-Platform` reports
 * the real platform either way.
 *
 * @param {string} userAgent
 */
export function brandUserAgent(userAgent) {
  // Extend the first comment -- the system-information field, `(X11;
  // Linux x86_64)` on this platform. A third subfield there is
  // unremarkable: Windows and Android ship more than two.
  const branded = userAgent.replace(
    /^([^(]*\()([^)]*)(\))/,
    (_, head, platform, close) => `${head}${platform}; ${UA_COMMENT_FIELDS}${close}`,
  );
  // Fallback for an unrecognized shape (no comment at all): identifying
  // in the refused position beats not identifying. Trailing product plus
  // contact comment, the bot convention Googlebot follows.
  return branded === userAgent ? `${userAgent} ${UA_PRODUCT}` : branded;
}

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

// High-entropy client-hint fields, i.e. the ones a site must ask for.
// Read together with the low-entropy set to reconstruct the browser's
// own metadata whole.
const HIGH_ENTROPY_HINTS = [
  "architecture",
  "bitness",
  "model",
  "platformVersion",
  "uaFullVersion",
  "fullVersionList",
  "wow64",
];

/**
 * Read the browser's own User-Agent Client Hint metadata, so a branded
 * UA override can carry it forward unchanged.
 *
 * `Network.setUserAgentOverride` without `userAgentMetadata` makes
 * Chromium send *no* `Sec-CH-UA*` headers at all -- a UA anomaly no
 * real browser exhibits (`unblocked-sessions`), and a capture-fidelity
 * hole besides: the recorded requests would lack headers the live app
 * sends. The metadata must therefore be truthful, which means asking
 * the browser rather than constructing it.
 *
 * `navigator.userAgentData` requires a secure context, which
 * `about:blank` is not; `file:` (which Chromium resolves to the
 * `file:///` root listing) is, and costs no temp file and no network
 * request.
 *
 * @param {Browser} browser
 * @returns {Promise<any>}
 */
async function userAgentMetadata(browser) {
  const probe = await browser.newPage();
  try {
    await probe.goto("file:");
    const hints = await probe.evaluate(
      async (keys) =>
        await /** @type {any} */ (navigator).userAgentData.getHighEntropyValues(
          keys,
        ),
      HIGH_ENTROPY_HINTS,
    );
    return {
      brands: hints.brands,
      fullVersionList: hints.fullVersionList,
      fullVersion: hints.uaFullVersion,
      platform: hints.platform,
      platformVersion: hints.platformVersion,
      architecture: hints.architecture,
      model: hints.model,
      mobile: hints.mobile,
      bitness: hints.bitness,
      wow64: hints.wow64,
    };
  } finally {
    await probe.close();
  }
}

/**
 * Adapt one puppeteer page to a `HostSession`: raw send plus blanket
 * event subscription, with the branded UA applied before any capture
 * domain is enabled.
 *
 * @param {Page} page
 * @param {string} brandedUA
 * @param {any} metadata
 * @returns {Promise<HostSession>}
 */
async function hostSession(page, brandedUA, metadata) {
  const cdp = await page.createCDPSession();
  await cdp.send("Network.setUserAgentOverride", {
    userAgent: brandedUA,
    userAgentMetadata: metadata,
  });
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
  const brandedUA = brandUserAgent(await browser.userAgent());
  const metadata = await userAgentMetadata(browser);

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
      session: (target) =>
        hostSession(/** @type {Page} */ (target), brandedUA, metadata),
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
    // Capture drives the Network domain itself; puppeteer's
    // HTTPRequest/HTTPResponse, the only casualties of turning its
    // network manager off, go unused here. Turning it off also stops
    // it from sending a metadata-less `Network.setUserAgentOverride`
    // to every session *it* attaches (see `userAgentMetadata` above),
    // which matters for the sessions we never override ourselves --
    // OOPIF frames, and new targets before capture attaches.
    networkEnabled: false,
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
  // A persistent profile restores the previous session's tabs. Only
  // this page and targets created after attach get wired for capture,
  // so a human who wandered into a restored tab would generate traffic
  // no session is listening to -- a silent miss. Close them, leaving
  // the capture window single-tabbed.
  const pages = await browser.pages();
  const page = pages[0] ?? (await browser.newPage());
  for (const stale of pages.slice(1)) {
    await stale.close().catch(() => {});
  }
  // Human may take any amount of time to complete login/capture.
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
  // The captured page may not be the window's front tab (e.g. a
  // restored blank tab sits in front of it); the human needs to see it.
  await page.bringToFront();

  const close = async () => {
    await browser.close().catch(() => {});
    await done;
  };

  return { page, browser, events, done, close };
}
