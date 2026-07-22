/**
 * `attachCapture`'s final drain must wait for requests that are still
 * in flight (sent but not yet finished/failed) at "Done Capturing" time
 * -- not just requests that already reached `loadingFinished`, which is
 * all `inFlight` tracked before this fix. The wait is bounded by an
 * injectable `drainGraceMs` so a request that never reaches a terminal
 * CDP event can't hang the drain forever.
 */
import { test, expect } from "./fixtures.mjs";
import { drainMessages, findRR } from "./_common/testing.mjs";

test("in-flight request completing within the grace period is captured", async ({
  startCapture,
  payloadServer,
}) => {
  const GENEROUS_GRACE_MS = 5000;
  const session = await startCapture({
    url: `${payloadServer.url}/`,
    drainGraceMs: GENEROUS_GRACE_MS,
  });

  // Fire-and-forget: don't await the fetch itself, so Done gets clicked
  // while the response is still in flight (headers/body not yet arrived).
  const RESPONSE_DELAY_MS = 300;
  const fireRequest = session.page.evaluate((d) => {
    fetch(`/payload?id=inflight&delay=${d}`).catch(() => {});
  }, RESPONSE_DELAY_MS);
  await Promise.all([fireRequest, session.page.click("#capture-done")]);

  const messages = await drainMessages(session);

  const rr = findRR(messages, "id=inflight");
  expect(rr, "response arriving after Done click, within grace, is captured").toBeTruthy();

  const rwbs = messages.filter((m) => m.method === "Network.requestWillBeSent");
  expect(rwbs.length, "requestWillBeSent events still pass through").toBeGreaterThan(0);
});

test("in-flight request completing within the DEFAULT grace period is captured", async ({
  startCapture,
  payloadServer,
}) => {
  // No drainGraceMs override -- this is the only test exercising the real
  // DRAIN_GRACE_MS constant rather than an injected value; a test that
  // always overrides it can't catch the constant itself regressing (e.g.
  // fat-fingered to 0).
  const session = await startCapture({ url: `${payloadServer.url}/` });

  const RESPONSE_DELAY_MS = 300;
  const fireRequest = session.page.evaluate((d) => {
    fetch(`/payload?id=default-grace&delay=${d}`).catch(() => {});
  }, RESPONSE_DELAY_MS);
  await Promise.all([fireRequest, session.page.click("#capture-done")]);

  const messages = await drainMessages(session);

  const rr = findRR(messages, "id=default-grace");
  expect(rr, "response arriving shortly after Done click is captured under the default grace period").toBeTruthy();
});

test("capture ends promptly once in-flight requests settle, not after the full grace period", async ({
  startCapture,
  payloadServer,
}) => {
  test.setTimeout(45_000);

  const HUGE_GRACE_MS = 30_000;
  const session = await startCapture({
    url: `${payloadServer.url}/`,
    drainGraceMs: HUGE_GRACE_MS,
  });

  // One finished request, one failed (mid-body abort), one redirected --
  // each exercises a different settlePending call site.
  const fireRequests = session.page.evaluate(() => {
    fetch("/payload?id=finished").catch(() => {});
    fetch("/abort-after-headers").catch(() => {});
    fetch("/redirect").catch(() => {});
  });
  await Promise.all([fireRequests, session.page.click("#capture-done")]);

  const start = Date.now();
  const messages = await drainMessages(session);
  const elapsed = Date.now() - start;

  expect(
    elapsed,
    `drain ended promptly (${elapsed}ms), not after the ${HUGE_GRACE_MS}ms grace period`,
  ).toBeLessThan(5000);
  expect(findRR(messages, "id=finished"), "finished request captured").toBeTruthy();
});

test("hung request does not block capture end past the grace period", async ({
  startCapture,
  payloadServer,
}) => {
  test.setTimeout(15_000);

  const SHORT_GRACE_MS = 300;
  const session = await startCapture({
    url: `${payloadServer.url}/`,
    drainGraceMs: SHORT_GRACE_MS,
  });

  // Server never responds to /hang at all -- this request never reaches
  // a terminal CDP event.
  const fireRequest = session.page.evaluate(() => {
    fetch("/hang").catch(() => {});
  });
  await Promise.all([fireRequest, session.page.click("#capture-done")]);

  const start = Date.now();
  const guard = new Promise((_, rej) =>
    setTimeout(() => rej(new Error("drain did not end after the grace period")), 10_000),
  );
  await Promise.race([drainMessages(session), guard]);
  const elapsed = Date.now() - start;

  expect(
    elapsed,
    `drain bounded by grace period (${elapsed}ms), not blocked forever by the hung request`,
  ).toBeLessThan(SHORT_GRACE_MS + 5000);
});
