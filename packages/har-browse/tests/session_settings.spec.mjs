/**
 * Per-CDP-session capture settings, applied at wire-up in the capture
 * core's `wireSession`. Both serve one motive: force client
 * state through the observable network, so a response the page uses is
 * a response the capture saw.
 *
 * - `Network.setCacheDisabled` -- an HTTP-cache hit reaches no server
 *   and yields no fetchable body.
 * - `Network.setBypassServiceWorker` -- a service worker's cache-first
 *   handler serves payload with no network traffic at all, and the
 *   worker's own target is invisible to per-page sessions
 *   (.claude/todo.kb/2026-07-23-001-*).
 *
 * The oracle in both tests is the server's `requestLog`: ground truth
 * for "the request actually crossed the network".
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages, findRR } from "./_common/testing.mjs";

test("HTTP-cacheable payload is refetched on revisit, not served from cache", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/` });

  const fetchTwice = async () => {
    await session.page.evaluate(() => fetch("/cacheable").then((r) => r.json()));
    await session.page.reload();
    await session.page.evaluate(() => fetch("/cacheable").then((r) => r.json()));
  };
  await fetchTwice();
  await session.page.click("#capture-done");
  const messages = await drainMessages(session);

  expect(
    payloadServer.requestLog.filter((r) => r.pathname === "/cacheable").length,
    "both fetches cross the network despite max-age=300",
  ).toBe(2);
  const cacheHits = messages.filter(
    (m) => m.method === "Network.requestServedFromCache",
  );
  expect(cacheHits, "no request is served from the browser cache").toEqual([]);
});

test("service-worker-mediated payload still crosses the network", async ({
  startCapture,
  payloadServer,
}) => {
  const session = await startCapture({ url: `${payloadServer.url}/sw-page` });

  const settled = () =>
    session.page.waitForFunction(
      () =>
        (document.getElementById("content")?.textContent ?? "").startsWith("sw:"),
      null,
      { timeout: 15_000 },
    );
  // Three loads, because only the third is unambiguous: the first
  // registers the worker (whether it claims this client before the
  // payload fetch is a race), the second is controlled from the start
  // and would populate the worker's cache, and the third is the one a
  // cache-first worker could answer entirely off-network.
  await settled();
  await session.page.reload();
  await settled();
  await session.page.reload();
  await settled();

  await session.page.click("#capture-done");
  const messages = await drainMessages(session);

  expect(
    payloadServer.requestLog.filter((r) => r.search.includes("id=sw")).length,
    "every payload fetch reaches the server, service worker notwithstanding",
  ).toBe(3);
  expect(
    await session.page.textContent("#content"),
    "the bypass leaves the page uncontrolled, so no fetch can be intercepted",
  ).toMatch(/^sw:false:/);
  expect(
    findRR(messages, "id=sw"),
    "and the capture holds the response",
  ).toBeTruthy();
});
