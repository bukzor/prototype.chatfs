import { createServer } from "node:http";

/**
 * Toy HTTP server for capture stress tests.
 *
 * - GET /payload?id=K&delay=D → JSON {id, n} where `n` is a per-response
 *   monotonic counter assigned at end-of-handler. Lets tests assert
 *   that the captured n-set equals {1..served} — gaps *within* the
 *   captured set, distinct from a plain served-vs-captured count.
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
  const requestLog = [];
  let payloadCount = 0;
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
    res.writeHead(200, { "content-type": "text/html" });
    res.end("<!doctype html><html><body>capture stress</body></html>");
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve()));
  const addr = server.address();
  if (typeof addr !== "object" || addr === null) {
    throw new Error(`unexpected server.address(): ${addr}`);
  }
  return {
    port: addr.port,
    requestLog,
    close: () => new Promise((resolve) => server.close(() => resolve())),
  };
}
