// @ts-check
import { mkdirSync } from "node:fs";
import { EventEmitter, on } from "node:events";
import { chromium } from "./playwright.mjs";
import { injectOverlay } from "./inject.mjs";

/** @typedef {{ method: string, params: any }} CDPEvent */
/** @typedef {import("playwright").Page} Page */
/** @typedef {import("playwright").BrowserContext} BrowserContext */

// Bounds the final drain (see `attachCapture`'s `done`): a request that
// never reaches a terminal CDP event (hung, or the CDP session dies
// mid-flight) would otherwise block shutdown forever, since the caller
// only closes the context after the events stream ends.
const DRAIN_GRACE_MS = 2000;

/**
 * Stream CDP events from an open page as `{method, params}` JSONL —
 * chrome-har's wire format. Response bodies attach at
 * `Network.responseReceived.params.response.body`
 * (+ `.encoding = "base64"` when applicable). Stream ends on injected
 * "Done" click or context close. Caller owns the browser lifecycle.
 *
 * @param {Page} page
 * @param {{ howto?: string, drainGraceMs?: number }} [opts]
 * @returns {Promise<{
 *   events: AsyncIterable<CDPEvent>,
 *   done: Promise<void>,
 * }>}
 */
export async function attachCapture(page, { howto, drainGraceMs = DRAIN_GRACE_MS } = {}) {
  const context = page.context();

  const emitter = new EventEmitter();
  // Subscribe before any CDP attachment: on() doesn't retroactively
  // capture events emitted before its iterator existed.
  const queue = on(emitter, "event", { close: ["end"] });
  /** @param {CDPEvent} msg */
  const enqueue = (msg) => emitter.emit("event", msg);

  // BARRIER's deferred-emit (see `onBindingCalled` below) snapshots
  // `inFlight` to wait out active body-fetches so consumed RRs land
  // before the BARRIER that names them — a narrow, fast-resolving set
  // by design. `pendingInFlight` is deliberately kept separate: it
  // tracks every request from the moment it's sent (see `pendingRequests`
  // below), which for a page mid-load can be hundreds of entries still
  // outstanding. Folding those into `inFlight` would make BARRIER wait
  // on unrelated, unfinished requests it never claimed to consume,
  // routinely blowing past `drainGraceMs` and dropping the BARRIER
  // event itself. The final drain waits on the union of both.
  /** @type {Set<Promise<unknown>>} */
  const inFlight = new Set();
  /** @type {Set<Promise<unknown>>} */
  const pendingInFlight = new Set();
  /** @template T @param {Promise<T>} pr @param {Set<Promise<unknown>>} [set] @returns {Promise<T>} */
  const track = (pr, set = inFlight) => {
    set.add(pr);
    pr.finally(() => set.delete(pr));
    return pr;
  };

  // A request is pending from the moment it's sent until it reaches a
  // terminal event (loadingFinished/loadingFailed) — a strictly earlier
  // and wider window than `awaitingBody` below, which only starts once
  // headers arrive. Tracking here (not just post-loadingFinished) is
  // what lets the final drain wait out a request that's still in flight
  // at "Done Capturing" time instead of dropping it with zero trace.
  /** @type {Map<string, () => void>} */
  const pendingRequests = new Map();
  /** @param {string} requestId */
  const settlePending = (requestId) => {
    const resolve = pendingRequests.get(requestId);
    if (resolve) {
      pendingRequests.delete(requestId);
      resolve();
    }
  };

  /** @param {Page} subject */
  const wireSession = async (subject) => {
    const session = await context.newCDPSession(subject);

    // RR arrives with headers; stashed by requestId, flushed on LF/LFail
    // with body attached. `getResponseBody` is one-shot per response.
    /** @type {Map<string, any>} */
    const awaitingBody = new Map();

    /** @param {any} lf */
    async function onLoadingFinished(lf) {
      const rr = awaitingBody.get(lf.requestId);
      awaitingBody.delete(lf.requestId);
      if (rr) {
        try {
          const body = await session.send("Network.getResponseBody", {
            requestId: lf.requestId,
          });
          rr.response.body = body.body;
          if (body.base64Encoded) rr.response.encoding = "base64";
        } catch {
          // 204 / redirect / no-body responses reject; emit bare.
        }
        enqueue({ method: "Network.responseReceived", params: rr });
      }
      enqueue({ method: "Network.loadingFinished", params: lf });
      settlePending(lf.requestId);
    }

    /** @param {any} lfail */
    function onLoadingFailed(lfail) {
      const rr = awaitingBody.get(lfail.requestId);
      awaitingBody.delete(lfail.requestId);
      if (rr) enqueue({ method: "Network.responseReceived", params: rr });
      enqueue({ method: "Network.loadingFailed", params: lfail });
      settlePending(lfail.requestId);
    }

    /** @param {any} params */
    function onBindingCalled(params) {
      // BARRIER snapshot-defer: hold emit until in-flight body-fetches at
      // CDP arrival have settled. Per-BARRIER snapshots; concurrent
      // BARRIERs serialize via allSettled's superset ordering.
      if (
        params.name === "harBrowseMark" &&
        params.payload?.startsWith?.("BARRIER:")
      ) {
        track(
          Promise.allSettled([...inFlight]).then(() =>
            enqueue({ method: "Runtime.bindingCalled", params }),
          ),
        );
      } else {
        enqueue({ method: "Runtime.bindingCalled", params });
      }
    }

    /** @param {any} p */
    function onRequestWillBeSent(p) {
      // CDP re-fires this for each redirect hop with the SAME requestId
      // -- guard so a single logical request gets exactly one tracked
      // promise, resolved once at its eventual terminal event.
      if (!pendingRequests.has(p.requestId)) {
        /** @type {() => void} */
        let resolve = () => {};
        /** @type {Promise<void>} */
        const pr = new Promise((res) => {
          resolve = res;
        });
        pendingRequests.set(p.requestId, resolve);
        track(pr, pendingInFlight);
      }
      enqueue({ method: "Network.requestWillBeSent", params: p });
    }

    /** @type {Record<string, (params: any) => void>} */
    const cdpHandlers = {
      "Network.requestWillBeSent": onRequestWillBeSent,
      "Network.responseReceived": (p) => awaitingBody.set(p.requestId, p),
      "Network.loadingFinished": (p) => track(onLoadingFinished(p)),
      "Network.loadingFailed": onLoadingFailed,
      "Runtime.bindingCalled": onBindingCalled,
    };

    // Blanket passthrough via emit-override: handlers special-case the
    // methods that need transformation; everything else (Page.*, Target.*,
    // etc.) flows through unchanged so downstream HAR builders see the
    // full event set. CDPSession extends EventEmitter internally — cast
    // through it to reach `.emit`, which isn't in playwright's public
    // surface.
    const sessionBus = /** @type {EventEmitter} */ (/** @type {unknown} */ (session));
    const origEmit = sessionBus.emit.bind(sessionBus);
    sessionBus.emit = function (name, ...args) {
      if (typeof name === "string" && name.includes(".")) {
        const params = args[0] ?? {};
        (cdpHandlers[name] ?? ((p) => enqueue({ method: name, params: p })))(params);
      }
      return origEmit(name, ...args);
    };

    await session.send("Network.enable");
    await session.send("Page.enable");
    await session.send("Runtime.enable");
    await session.send("Runtime.addBinding", { name: "harBrowseMark" });
  };

  await wireSession(page);
  context.on("page", (p) => track(wireSession(p)));

  await injectOverlay(page, { howto });

  // Drain inFlight (body-fetches + deferred BARRIERs) before "end" so
  // their emits land in the queue first.
  const done = Promise.race([
    page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
    ),
    context.waitForEvent("close"),
  ])
    .catch(() => {})
    .finally(async () => {
      await Promise.race([
        Promise.allSettled([...inFlight, ...pendingInFlight]),
        new Promise((resolve) => setTimeout(resolve, drainGraceMs)),
      ]);
      emitter.emit("end");
    })
    .then(() => {});

  const events = (async function* () {
    for await (const [msg] of queue) yield msg;
  })();

  return { events, done };
}

/**
 * Launch a persistent-context browser, navigate, and return a capture
 * session. Per-profile state persists under `profileDir`.
 *
 * @param {{
 *   url: string,
 *   profileDir: string,
 *   howto?: string,
 *   headless?: boolean,
 *   drainGraceMs?: number,
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
}) {
  mkdirSync(profileDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless,
  });
  // Human may take any amount of time to complete login/capture.
  context.setDefaultTimeout(0);

  const page = context.pages()[0] ?? (await context.newPage());
  const { events, done } = await attachCapture(page, { howto, drainGraceMs });
  await page.goto(url, { waitUntil: "commit" });

  const close = async () => {
    await context.close().catch(() => {});
    await done;
  };

  return { page, context, events, done, close };
}
