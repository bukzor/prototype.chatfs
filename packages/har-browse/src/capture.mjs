// @ts-check
// Venue-agnostic capture semantics: pending-ledger, drain, BARRIER,
// body attachment. Everything browser-specific reaches this module
// through the `CaptureHost` seam below -- "CDP sessions + events per
// target" plus a cut signal. `host_playwright.mjs` is the current
// shell behind the seam.
//
// BARRIER protocol: a page-side `harBrowseMark("BARRIER:...")` binding
// call must land in the stream *after* every response the page had
// consumed when it fired. Mechanics: `onBindingCalled` snapshots
// `inFlight` via spread and defers the BARRIER's emit behind
// `Promise.allSettled` of that snapshot; concurrent BARRIERs serialize
// via allSettled's superset ordering. Formal invariant:
// `tests/barrier_consumed.spec.mjs`.
import { EventEmitter, on } from "node:events";

/** @typedef {{ method: string, params: any }} CDPEvent */

/**
 * One target's CDP session.
 *
 * @typedef {object} HostSession
 * @property {(method: string, params?: any) => Promise<any>} send
 * @property {(cb: (method: string, params: any) => void) => void} onEvent
 *   Blanket subscription: every CDP event on this session, no filter.
 */

/**
 * The host seam.
 *
 * @typedef {object} CaptureHost
 * @property {unknown} initialTarget
 * @property {(cb: (target: unknown) => void) => void} onTarget
 *   Targets appearing after attach (popups). The callback's returned
 *   promise is tracked by the drain, so wiring still in progress at
 *   the cut is awaited, not raced.
 * @property {(target: unknown) => Promise<HostSession>} session
 * @property {Promise<void>} cut
 *   Resolves at the capture cut -- Done click or window close. Never
 *   rejects.
 */

// Bounds the final drain (see `captureStream`'s `done`): a request that
// never reaches a terminal CDP event (hung, or the CDP session dies
// mid-flight) would otherwise block shutdown forever, since the caller
// only closes the browser after the events stream ends.
const DRAIN_GRACE_MS = 2000;

/**
 * Stream CDP events from a host's targets as `{method, params}` JSONL --
 * chrome-har's wire format. Response bodies attach at
 * `Network.responseReceived.params.response.body`
 * (+ `.encoding = "base64"` when applicable). Stream ends after
 * `host.cut` resolves and the drain settles. Caller owns the browser
 * lifecycle.
 *
 * @param {CaptureHost} host
 * @param {{ drainGraceMs?: number }} [opts]
 * @returns {Promise<{
 *   events: AsyncIterable<CDPEvent>,
 *   done: Promise<void>,
 * }>}
 */
export async function captureStream(host, { drainGraceMs = DRAIN_GRACE_MS } = {}) {
  const emitter = new EventEmitter();
  // Subscribe before any CDP attachment: on() doesn't retroactively
  // capture events emitted before its iterator existed.
  const queue = on(emitter, "event", { close: ["end"] });
  // Post-"end" the queue is closed and the event is unrecoverable; a
  // silent drop here would be invisible data loss, so name it on stderr.
  let ended = false;
  /** @param {CDPEvent} msg */
  const enqueue = (msg) => {
    if (ended) {
      process.stderr.write(
        `har-browse: dropped event after stream end: ${msg.method}\n`,
      );
      return;
    }
    emitter.emit("event", msg);
  };

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

  /** @param {unknown} target */
  const wireSession = async (target) => {
    const session = await host.session(target);

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

    // Blanket passthrough: handlers special-case the methods that need
    // transformation; everything else (Page.*, Target.*, etc.) flows
    // through unchanged so downstream HAR builders see the full event
    // set.
    session.onEvent((method, params) => {
      (cdpHandlers[method] ?? ((p) => enqueue({ method, params: p })))(params);
    });

    await session.send("Network.enable");
    // Force client state through the observable network: full bodies
    // instead of cache hits (standard for HAR tooling), and
    // network-direct fetches so service-worker-mediated traffic shows
    // up as ordinary page-session events (interim mitigation for the
    // non-page-target gap — todo.kb/2026-07-23-001-*).
    await session.send("Network.setCacheDisabled", { cacheDisabled: true });
    await session.send("Network.setBypassServiceWorker", { bypass: true });
    await session.send("Page.enable");
    await session.send("Runtime.enable");
    await session.send("Runtime.addBinding", { name: "harBrowseMark" });
  };

  await wireSession(host.initialTarget);
  host.onTarget((t) => track(wireSession(t)));

  // Drain inFlight (body-fetches + deferred BARRIERs) before "end" so
  // their emits land in the queue first.
  const done = host.cut
    .finally(async () => {
      await Promise.race([
        Promise.allSettled([...inFlight, ...pendingInFlight]),
        new Promise((resolve) => setTimeout(resolve, drainGraceMs)),
      ]);
      ended = true;
      emitter.emit("end");
    })
    .then(() => {});

  const events = (async function* () {
    for await (const [msg] of queue) yield msg;
  })();

  return { events, done };
}
