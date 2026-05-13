import { mkdirSync } from "node:fs";
import { EventEmitter, on } from "node:events";
import { chromium } from "./playwright.mjs";
import { injectOverlay } from "./inject.mjs";

/**
 * Attach Chrome DevTools Protocol capture to an already-open page. Streams
 * CDP events as `{method, params}` — the wire format `chrome-har` and other
 * CDP consumers expect. Response bodies are attached to
 * `Network.responseReceived.params.response` as `.body`
 * (+ `.encoding = "base64"` when applicable), per chrome-har's convention.
 *
 * The stream ends when the user clicks the injected "Done" button or the
 * context closes. The browser's lifecycle is the caller's responsibility;
 * use `startCapture` for the convenience-wrapped version.
 *
 * @param {import("playwright").Page} page
 * @param {object} [opts]
 * @param {string} [opts.howto]  pre-read howto content (string, not path)
 * @returns {Promise<{
 *   events: AsyncIterable<{method: string, params: object}>,
 *   done: Promise<void>,
 * }>}
 */
export async function attachCapture(page, { howto } = {}) {
  const context = page.context();

  const out = new EventEmitter();
  // Subscribe BEFORE any CDP attachment so events emitted during setup
  // and navigation are buffered, not dropped. on() does not retroactively
  // capture events emitted before the iterator existed.
  const stream = on(out, "event", { close: ["end"] });
  const emit = (msg) => out.emit("event", msg);

  // Drain tracker: body-fetch lookups (and deferred BARRIER emits) need
  // to finish before we emit "end".
  const pending = new Set();
  const track = (pr) => {
    pending.add(pr);
    pr.finally(() => pending.delete(pr));
    return pr;
  };

  const attach = async (p) => {
    const session = await context.newCDPSession(p);

    // `responseReceived` arrives with headers but not body; held here per
    // requestId until the matching `loadingFinished` (or `loadingFailed`)
    // lets us fetch and attach the body. `Network.getResponseBody` is an
    // effectful getter — a single call per response consumes the buffer;
    // do not double-subscribe it.
    const awaitingBody = new Map();

    async function emitWithBody(lf) {
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
        emit({ method: "Network.responseReceived", params: rr });
      }
      emit({ method: "Network.loadingFinished", params: lf });
    }

    function emitOnFail(lfail) {
      const rr = awaitingBody.get(lfail.requestId);
      awaitingBody.delete(lfail.requestId);
      if (rr) emit({ method: "Network.responseReceived", params: rr });
      emit({ method: "Network.loadingFailed", params: lfail });
    }

    function emitBinding(params) {
      // Snapshot body-fetches in flight at BARRIER's CDP arrival; defer
      // the bindingCalled emit until all settle. Per-target CDP FIFO
      // guarantees any loadingFinished that preceded this bindingCalled
      // has already enqueued its body-fetch into `pending`. Reentrant:
      // each BARRIER takes its own snapshot, and Promise.allSettled on
      // a superset can only resolve at-or-after its subset's, so
      // serialization between concurrent BARRIERs is structural.
      if (
        params.name === "harBrowseMark" &&
        params.payload?.startsWith?.("BARRIER:")
      ) {
        track(
          Promise.allSettled([...pending]).then(() =>
            emit({ method: "Runtime.bindingCalled", params }),
          ),
        );
      } else {
        emit({ method: "Runtime.bindingCalled", params });
      }
    }

    // Per-method dispatch. The `else` branch in the override is blanket
    // passthrough — keeps chrome-har's Network/Page/Target events flowing
    // without enumerating them.
    const handlers = {
      "Network.responseReceived": (p) => awaitingBody.set(p.requestId, p),
      "Network.loadingFinished": (p) => track(emitWithBody(p)),
      "Network.loadingFailed": (p) => emitOnFail(p),
      "Runtime.bindingCalled": (p) => emitBinding(p),
    };

    const origEmit = session.emit.bind(session);
    session.emit = function (name, ...args) {
      if (typeof name === "string" && name.includes(".")) {
        const params = args[0] ?? {};
        (handlers[name] ?? ((p) => emit({ method: name, params: p })))(params);
      }
      return origEmit(name, ...args);
    };

    await session.send("Network.enable");
    await session.send("Page.enable");
    await session.send("Runtime.enable");
    await session.send("Runtime.addBinding", { name: "harBrowseMark" });
  };

  await attach(page);
  context.on("page", (p) => track(attach(p)));

  await injectOverlay(page, { howto });

  // Termination: Done click or window close. Drain in-flight body-fetches
  // (and any deferred BARRIER emits) before signalling end so their emits
  // land in the queue first.
  const done = Promise.race([
    page.waitForFunction(
      () => document.getElementById("capture-done")?.dataset.clicked === "true",
    ),
    context.waitForEvent("close"),
  ])
    .catch(() => {})
    .finally(async () => {
      await Promise.allSettled([...pending]);
      out.emit("end");
    });

  const events = (async function* () {
    for await (const [msg] of stream) yield msg;
  })();

  return { events, done };
}

/**
 * Launch a persistent-context browser, navigate to `url`, and return a
 * capture session. Thin convenience wrapper over `attachCapture` that
 * also manages the browser lifecycle. Per-profile state persists under
 * `profileDir`.
 *
 * @param {object} opts
 * @param {string} opts.url
 * @param {string} opts.profileDir
 * @param {string} [opts.howto]
 * @param {boolean} [opts.headless=false]
 * @returns {Promise<{
 *   page: import("playwright").Page,
 *   context: import("playwright").BrowserContext,
 *   events: AsyncIterable<{method: string, params: object}>,
 *   done: Promise<void>,
 *   close: () => Promise<void>,
 * }>}
 */
export async function startCapture({ url, profileDir, howto, headless = false }) {
  mkdirSync(profileDir, { recursive: true });

  const context = await chromium.launchPersistentContext(profileDir, {
    headless,
  });
  // Disable default timeouts on everything the context owns: page waits,
  // page.goto, and context.waitForEvent("close") — the human may take any
  // amount of time to complete login/capture.
  context.setDefaultTimeout(0);

  const page = context.pages()[0] ?? (await context.newPage());
  const { events, done } = await attachCapture(page, { howto });
  await page.goto(url, { waitUntil: "commit" });

  const close = async () => {
    await context.close().catch(() => {});
    await done;
  };

  return { page, context, events, done, close };
}
