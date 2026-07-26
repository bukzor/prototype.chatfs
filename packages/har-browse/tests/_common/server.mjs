import { createServer } from "node:http";

/**
 * Toy HTTP server for capture stress tests.
 *
 * - GET /payload?id=K&delay=D → JSON {id, n} where `n` is a per-response
 *   monotonic counter assigned at end-of-handler. Lets tests assert
 *   that the captured n-set equals {1..served} — gaps *within* the
 *   captured set, distinct from a plain served-vs-captured count.
 * - GET /hang → accepts the connection, never responds. For tests that
 *   need a request that never reaches a terminal CDP event.
 * - GET /redirect → 302 to /payload?id=redirected. For tests exercising
 *   requestId reuse across CDP's repeated requestWillBeSent per hop.
 * - GET /hydrate → HTML page that persists /payload to IndexedDB: on
 *   first load it fetches `/payload?id=hydrate` and stores the response;
 *   on later loads it renders from the stored copy *without* fetching.
 *   The decision runs in an inline parse-time script (not deferred) so a
 *   storage-clear issued after navigation deterministically loses the
 *   race — see docs/dev/mutation-testing.kb/clear-origin-storage-after-goto.md.
 *   `#content` text starts with "fetched:" or "hydrated:" accordingly.
 * - GET /cacheable → JSON {n} with `cache-control: max-age=300`. A
 *   second fetch is served from the HTTP cache -- and never reaches
 *   this server -- unless the capture disabled caching.
 * - GET /sw-page, GET /sw.js → page registering a cache-first service
 *   worker for `/payload?id=sw`. Once the worker controls the page, a
 *   refetch is served from Cache Storage without network traffic unless
 *   the capture bypasses service workers. `#content` reports
 *   "sw:<controlled>:<n>" once the payload has been (re)fetched.
 * - GET /trusted-types → minimal HTML served with
 *   `Content-Security-Policy: require-trusted-types-for 'script'`,
 *   matching aistudio.google.com's enforcement. For tests exercising
 *   injectOverlay() under a Trusted Types sink restriction.
 * - Anything else → minimal HTML for page navigation.
 *
 * Every request appends to `requestLog`, the server-side ground truth
 * for completeness oracles.
 *
 * @returns {Promise<{
 *   port: number,
 *   requestLog: Array<{pathname: string, search: string, time: number}>,
 *   close: () => Promise<void>,
 * }>}
 */
export async function startServer() {
  /** @type {Array<{pathname: string, search: string, time: number}>} */
  const requestLog = [];
  let payloadCount = 0;

  // `server.close()` waits for open connections to end before its
  // callback fires -- /hang deliberately never ends one. Track sockets
  // and destroy stragglers so teardown isn't held hostage by it.
  /** @type {Set<import("node:net").Socket>} */
  const sockets = new Set();

  const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    requestLog.push({
      pathname: url.pathname,
      search: url.search,
      time: Date.now(),
    });
    if (url.pathname === "/payload") {
      const id = url.searchParams.get("id") ?? "";
      const delay = Number(url.searchParams.get("delay") ?? 0);
      if (delay > 0) await new Promise((r) => setTimeout(r, delay));
      const n = ++payloadCount;
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ id, n }));
      return;
    }
    if (url.pathname === "/hang") {
      // Never call res.end() or even flushHeaders() -- the request sits
      // open until the client (or test teardown) gives up on it.
      return;
    }
    if (url.pathname === "/redirect") {
      res.writeHead(302, { location: "/payload?id=redirected" });
      res.end();
      return;
    }
    if (url.pathname === "/hydrate") {
      res.writeHead(200, { "content-type": "text/html" });
      res.end(`<!doctype html>
<html><body><div id="content">loading</div>
<script>
const open = indexedDB.open("hydrate", 1);
open.onupgradeneeded = () => open.result.createObjectStore("kv");
open.onsuccess = () => {
  const db = open.result;
  const get = db.transaction("kv", "readonly").objectStore("kv").get("payload");
  get.onsuccess = async () => {
    let data = get.result;
    let how = "hydrated";
    if (data === undefined) {
      how = "fetched";
      data = await (await fetch("/payload?id=hydrate")).json();
      db.transaction("kv", "readwrite").objectStore("kv").put(data, "payload");
    }
    document.getElementById("content").textContent =
      how + ": " + JSON.stringify(data);
  };
};
</script></body></html>`);
      return;
    }
    if (url.pathname === "/cacheable") {
      res.writeHead(200, {
        "content-type": "application/json",
        "cache-control": "max-age=300",
      });
      res.end(JSON.stringify({ n: ++payloadCount }));
      return;
    }
    if (url.pathname === "/sw.js") {
      res.writeHead(200, { "content-type": "application/javascript" });
      res.end(`
self.addEventListener("install", (e) => e.waitUntil(self.skipWaiting()));
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (e) => {
  if (!e.request.url.includes("id=sw")) return;
  e.respondWith((async () => {
    const cache = await caches.open("sw-payload");
    const hit = await cache.match(e.request);
    if (hit) return hit;
    const res = await fetch(e.request);
    await cache.put(e.request, res.clone());
    return res;
  })());
});
`);
      return;
    }
    if (url.pathname === "/sw-page") {
      res.writeHead(200, { "content-type": "text/html" });
      res.end(`<!doctype html>
<html><body><div id="content">loading</div>
<script>
(async () => {
  await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  const data = await (await fetch("/payload?id=sw")).json();
  document.getElementById("content").textContent =
    "sw:" + !!navigator.serviceWorker.controller + ":" + data.n;
})();
</script></body></html>`);
      return;
    }
    if (url.pathname === "/trusted-types") {
      res.writeHead(200, {
        "content-type": "text/html",
        "content-security-policy": "require-trusted-types-for 'script'",
      });
      res.end("<!doctype html><html><body>trusted types</body></html>");
      return;
    }
    if (url.pathname === "/abort-after-headers") {
      // Send headers + a partial body, then forcibly tear down the
      // socket before EOF. Browser sees: responseReceived (headers)
      // followed by loadingFailed (transport error) — the regime that
      // exercises `onLoadingFailed`'s stashed-RR flush.
      res.writeHead(200, { "content-type": "application/json" });
      res.flushHeaders();
      // Small delay so headers reach the wire before the RST.
      setTimeout(() => res.socket?.destroy(), 10);
      return;
    }
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<!doctype html><html><body>capture stress</body></html>");
  });
  server.on("connection", (socket) => {
    sockets.add(socket);
    socket.on("close", () => sockets.delete(socket));
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const addr = server.address();
  if (typeof addr !== "object" || addr === null) {
    throw new Error(`unexpected server.address(): ${addr}`);
  }
  return {
    port: addr.port,
    requestLog,
    close: () =>
      new Promise((resolve) => {
        server.close(() => resolve());
        for (const socket of sockets) socket.destroy();
      }),
  };
}
