// @ts-check
// Playwright host shell behind `capture.mjs`'s CaptureHost seam:
// launcher, profile flow, per-target CDP session adaptation, overlay
// install, and the cut race (Done click / window close). Ratified for
// replacement by puppeteer-core (todo.kb/2026-07-23-002-*) -- the
// semantics core stays; only this shell swaps.
import { mkdirSync } from "node:fs";
import { EventEmitter } from "node:events";
import { chromium } from "./playwright.mjs";
import { injectOverlay } from "./inject.mjs";
import { captureStream } from "./capture.mjs";

/** @typedef {import("./capture.mjs").CDPEvent} CDPEvent */
/** @typedef {import("./capture.mjs").HostSession} HostSession */
/** @typedef {import("playwright").Page} Page */
/** @typedef {import("playwright").BrowserContext} BrowserContext */

/**
 * Adapt one Playwright page to a `HostSession`: raw send plus blanket
 * event subscription.
 *
 * @param {BrowserContext} context
 * @param {Page} subject
 * @returns {Promise<HostSession>}
 */
async function hostSession(context, subject) {
  const cdp = await context.newCDPSession(subject);

  // Blanket subscription via emit-override: playwright's public
  // CDPSession surface only exposes per-method listeners. CDPSession
  // extends EventEmitter internally — cast through it to reach `.emit`.
  /** @type {Array<(method: string, params: any) => void>} */
  const listeners = [];
  const bus = /** @type {EventEmitter} */ (/** @type {unknown} */ (cdp));
  const origEmit = bus.emit.bind(bus);
  bus.emit = function (name, ...args) {
    if (typeof name === "string" && name.includes(".")) {
      const params = args[0] ?? {};
      for (const cb of listeners) cb(name, params);
    }
    return origEmit(name, ...args);
  };

  return {
    send: (method, params) =>
      cdp.send(/** @type {any} */ (method), params),
    onEvent: (cb) => listeners.push(cb),
  };
}

/**
 * Wire capture onto an existing Playwright page. Stream ends on
 * injected "Done" click or context close. Caller owns the browser
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
  const context = page.context();

  /** @type {() => void} */
  let resolveCut = () => {};
  /** @type {Promise<void>} */
  const cut = new Promise((res) => {
    resolveCut = res;
  });

  const { events, done } = await captureStream(
    {
      initialTarget: page,
      onTarget: (cb) => context.on("page", cb),
      session: (target) => hostSession(context, /** @type {Page} */ (target)),
      cut,
    },
    { drainGraceMs },
  );

  await injectOverlay(page, { howto });

  Promise.race([
    page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
    ),
    context.waitForEvent("close"),
  ])
    .catch(() => {})
    .then(resolveCut);

  return { events, done };
}

/**
 * Launch a persistent-context browser, navigate, and return a capture
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
 *   context: BrowserContext,
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

  const context = await chromium.launchPersistentContext(profileDir, {
    headless,
  });
  // Human may take any amount of time to complete login/capture.
  context.setDefaultTimeout(0);

  const page = context.pages()[0] ?? (await context.newPage());
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
    const session = await context.newCDPSession(page);
    await session.send("Storage.clearDataForOrigin", {
      origin: new URL(url).origin,
      storageTypes: "indexeddb,cache_storage",
    });
    await session.detach();
  }
  await page.goto(url, { waitUntil: "commit" });

  const close = async () => {
    await context.close().catch(() => {});
    await done;
  };

  return { page, context, events, done, close };
}
