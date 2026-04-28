import { mkdirSync } from "node:fs";
import { EventEmitter, on } from "node:events";
import { chromium } from "./playwright.mjs";
import { injectOverlay } from "./inject.mjs";

/**
 * Launch a persistent-context browser and expose a Chrome DevTools Protocol
 * event stream. Each event is `{method, params}` — the wire format that
 * `chrome-har` and other CDP-consuming tools expect. Response bodies are
 * attached to `Network.responseReceived.params.response` as `.body`
 * (+ `.encoding = "base64"` when applicable), per chrome-har's convention.
 *
 * Returns a session: callers interact with `page` directly, drain `events`,
 * and call `close()` when finished. The `events` iterable ends when the
 * user clicks the injected "Done" button, closes the window, or the
 * caller invokes `close()`.
 *
 * @param {object} opts
 * @param {string} opts.url
 * @param {string} opts.profileDir
 * @param {string} [opts.howto]  pre-read howto content (string, not path)
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

  let contextClosed = false;
  context.once("close", () => {
    contextClosed = true;
  });

  const out = new EventEmitter();
  // Subscribe BEFORE any CDP attachment so events emitted during setup
  // and navigation are buffered, not dropped. on() does not retroactively
  // capture events emitted before the iterator existed.
  const stream = on(out, "event", { close: ["end"] });
  const emit = (msg) => out.emit("event", msg);

  // Drain tracker: body-fetch lookups need to finish before we emit "end".
  const pending = new Set();
  const track = (pr) => {
    pending.add(pr);
    pr.finally(() => pending.delete(pr));
  };

  const attach = async (p) => {
    const session = await context.newCDPSession(p);

    // Blanket passthrough in chrome-har's `{method, params}` shape.
    // `responseReceived` is held per requestId and flushed from
    // `loadingFinished` with body attached at `params.response.body`.
    // `Network.getResponseBody` is an effectful getter — a single call
    // per response consumes the buffer; do not double-subscribe it.
    const held = new Map();
    const origEmit = session.emit.bind(session);
    session.emit = function (name, ...args) {
      if (typeof name !== "string" || !name.includes(".")) {
        return origEmit(name, ...args);
      }
      const params = args[0] ?? {};
      if (name === "Network.responseReceived") {
        held.set(params.requestId, params);
      } else if (name === "Network.loadingFinished") {
        const response = held.get(params.requestId);
        held.delete(params.requestId);
        track(
          (async () => {
            if (response) {
              try {
                const body = await session.send("Network.getResponseBody", {
                  requestId: params.requestId,
                });
                response.response.body = body.body;
                if (body.base64Encoded) response.response.encoding = "base64";
              } catch {
                // 204 / redirect / no-body responses reject; emit bare.
              }
              emit({ method: "Network.responseReceived", params: response });
            }
            emit({ method: name, params });
          })(),
        );
      } else if (name === "Network.loadingFailed") {
        const response = held.get(params.requestId);
        held.delete(params.requestId);
        if (response) {
          emit({ method: "Network.responseReceived", params: response });
        }
        emit({ method: name, params });
      } else {
        emit({ method: name, params });
      }
      return origEmit(name, ...args);
    };

    await session.send("Network.enable");
    await session.send("Page.enable");
  };

  const page = context.pages()[0] ?? (await context.newPage());

  context.on("page", (p) => track(attach(p)));
  await attach(page);

  await injectOverlay(page, { howto });
  await page.goto(url, { waitUntil: "commit" });

  // Termination: Done click or window close. Drain in-flight body-fetches
  // before signalling end so their emits land in the queue first.
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

  const close = async () => {
    if (!contextClosed) await context.close();
    await done;
  };

  return { page, context, events, done, close };
}
