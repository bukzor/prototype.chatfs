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
// so operators can recognize this tool's traffic. Several spellings,
// because each place a disclosure can go accepts a different grammar
// (survey: `design.kb/040-design.kb/self-identification.kb/`).
//
// A User-Agent's two positions differ per RFC 9110 §10.1.5: inside a
// `comment` the text is free-form ctext, conventionally `; `-separated;
// as a `product` the name and version must be `token`s, and `;` and
// `:` are not token characters -- so the contact URL needs a comment of
// its own out there.
const UA_COMMENT_FIELDS = `${pkg.name}/${pkg.version}; +${pkg.homepage}`;
const UA_PRODUCT = `${pkg.name}/${pkg.version} (+${pkg.homepage})`;

// The client-hint brand list takes a third: significant version only in
// `brands`, full version in `fullVersionList`, per the two lists'
// definitions. Both or neither -- a token in one and not the other is
// an inconsistency more conspicuous than the disclosure it carries.
const UA_BRAND = { brand: pkg.name, version: pkg.version.split(".")[0] };
const UA_BRAND_FULL = { brand: pkg.name, version: pkg.version };

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

// Run without a visible surface, while remaining the browser we would
// otherwise be. `--ozone-platform` selects a display *backend*; it is
// not `--headless`, which is a mode and rewrites the User-Agent.
//
// The other two flags are not optional decoration. Without
// `--window-size` the viewport is 0x0, and without `--screen-info` the
// `screen` object reports 1x1 -- a value no real display has, and the
// only measured anomaly this configuration would otherwise carry. Given
// both, every property we know how to check matches a headful run:
// User-Agent, client-hint brands, `requestAnimationFrame`, and the real
// GPU renderer. Measured by the sibling script of the design note above.
const WINDOWLESS_SCREEN = { width: 1440, height: 960 };
const WINDOWLESS_WINDOW = { width: 1280, height: 900 };
export const WINDOWLESS_ARGS = [
  "--ozone-platform=headless",
  `--window-size=${WINDOWLESS_WINDOW.width},${WINDOWLESS_WINDOW.height}`,
  `--screen-info={0,0 ${WINDOWLESS_SCREEN.width}x${WINDOWLESS_SCREEN.height}}`,
];

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
 * UA override can carry it forward with only our own brand added.
 *
 * `Network.setUserAgentOverride` without `userAgentMetadata` makes
 * Chromium send *no* `Sec-CH-UA*` headers at all -- a UA anomaly no
 * real browser exhibits (`unblocked-sessions`), and a capture-fidelity
 * hole besides: the recorded requests would lack headers the live app
 * sends. The metadata must therefore be truthful, which means asking
 * the browser rather than constructing it.
 *
 * The brand list is the one field we add to rather than pass through: a
 * site that reads only client hints would otherwise see no disclosure
 * at all, the UA comment being invisible to it. The list is built for
 * this -- unordered, extensible, and already carrying a GREASE entry
 * sites must tolerate -- and it is measured-compatible with the gate
 * that rules out a trailing UA product
 * (`design.kb/040-design.kb/self-identification.kb/`).
 *
 * `navigator.userAgentData` requires a secure context, which
 * `about:blank` is not; `file:` (which Chromium resolves to the
 * `file:///` root listing) is, and costs no temp file and no network
 * request.
 *
 * @param {Browser} browser
 * @returns {Promise<any>}
 */
export async function userAgentMetadata(browser) {
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
      brands: [...hints.brands, UA_BRAND],
      fullVersionList: [...hints.fullVersionList, UA_BRAND_FULL],
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
 * `windowless` drops the visible surface without altering the browser.
 * It is emphatically *not* puppeteer's `headless`, which is a mode, and
 * which rewrites the User-Agent's browser product to `HeadlessChrome`
 * -- that mode was removed from this package for exactly that reason
 * (`design.kb/040-design.kb/self-identification.kb/headless-changes-the-agent.md`).
 * This is a display *backend*: same binary, same mode, same User-Agent,
 * same brands, working `requestAnimationFrame`, real GPU. Do not
 * "simplify" it into `headless: true`.
 *
 * There is no Done button to click without a surface, so a windowless
 * capture ends only when its consumer closes the stream or the process
 * dies. That is the honest use: unattended runs and the test suite,
 * where the correct human interaction is none.
 *
 * @param {{
 *   url: string,
 *   profileDir: string,
 *   howto?: string,
 *   drainGraceMs?: number,
 *   clearOriginStorage?: boolean,
 *   windowless?: boolean,
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
  drainGraceMs,
  clearOriginStorage = false,
  windowless = false,
}) {
  mkdirSync(profileDir, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: await executablePath(),
    userDataDir: profileDir,
    headless: false,
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
      ...(windowless ? WINDOWLESS_ARGS : []),
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
