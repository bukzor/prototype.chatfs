/**
 * Causal-watermark adversarial oracle.
 *
 * Under adversarial concurrency (most fetches still in flight at marker
 * emit time), the SPECIFIC `Network.responseReceived` whose body the
 * page consumed before BARRIER must appear at a strictly earlier JSONL
 * index than the BARRIER event. Subset-of-events form: only the
 * consumed RR needs to precede; the other ~N-1 may emit after.
 *
 * Why this holds, given commit 1's snapshot-defer:
 *
 *  - The renderer fires the FIRST .then callback after the network
 *    service has delivered that response's body. The body delivery is
 *    downstream of Network.loadingFinished, so LF for that response is
 *    already enqueued in our CDP session before the bindingCalled.
 *  - capture.mjs has by then started the body-fetch for that response
 *    (kicked off from its LF handler) and added the promise to
 *    `pending`.
 *  - On the bindingCalled for "BARRIER:…", capture.mjs snapshots
 *    `pending` and defers the BARRIER emit until allSettled. The
 *    consumed response's body-fetch is in that snapshot, so its RR
 *    emit lands strictly before BARRIER.
 *
 * The ~N-1 other fetches are still in flight at BARRIER's CDP arrival
 * — their LF hasn't reached us yet, so their body-fetches aren't in
 * the snapshot, and their RR may emit after BARRIER (or not at all,
 * if end fires before they land).
 *
 * Awaiting `Promise.all` of every fetch would defeat the test: by the
 * time we click capture-done, every LF has arrived at the session, every
 * body-fetch has been triggered, and the drain in capture.mjs's
 * `done.finally` waits on all of them — collapsing the test into
 * barrier_smoke's all-form invariant. To preserve the subset regime
 * we await only the first 1%, leaving ~99% genuinely in flight.
 */
import { test, expect } from "./fixtures.mjs";
import { startServer } from "./_common/server.mjs";

const N = 500;
const AWAIT_COUNT = Math.max(1, Math.floor(N * 0.01));

/**
 * Two-stage bound: warn (annotation + stderr) if value > warnAt,
 * hard fail via expect() if value > failAt. Use with `failAt = 2 * warnAt`
 * to give a graceful tightening window before the regression becomes a
 * test failure.
 */
function bound({ name, value, warnAt, failAt }, testInfo) {
  if (value > warnAt && value <= failAt) {
    const msg = `${name}=${value} above warn ${warnAt} (fails above ${failAt})`;
    console.warn(`WARN: ${msg}`);
    testInfo.annotations.push({ type: "warning", description: msg });
  }
  expect(value, `${name}=${value} above fail threshold ${failAt}`).toBeLessThanOrEqual(
    failAt,
  );
}

test("causal-watermark: consumed RR precedes BARRIER", async (
  { startCapture },
  testInfo,
) => {
  const server = await startServer();
  try {
    const session = await startCapture({
      url: `http://127.0.0.1:${server.port}/`,
    });

    await session.page.evaluate(
      async ({ n, awaitCount }) => {
        let highWater = 0;
        const all = [];
        for (let i = 0; i < n; i++) {
          all.push(
            fetch(`/payload?id=${i}`)
              .then((r) => r.json())
              .then(({ n: rn }) => {
                if (rn > highWater) highWater = rn;
              }),
          );
        }
        // Wait for the first 1% to settle so highWater is non-trivial,
        // then snapshot it into BARRIER. The remaining ~99% stay in
        // flight — that's the adversarial condition under test.
        await Promise.all(all.slice(0, awaitCount));
        window.harBrowseMark(
          "BARRIER:" + JSON.stringify({ watermark: highWater }),
        );
      },
      { n: N, awaitCount: AWAIT_COUNT },
    );

    await session.page.click("#capture-done");

    const messages = [];
    for await (const msg of session.events) messages.push(msg);

    // Assertion 1: BARRIER bindingCalled landed in the stream.
    const barrierIdx = messages.findIndex(
      (m) =>
        m.method === "Runtime.bindingCalled" &&
        m.params?.name === "harBrowseMark" &&
        typeof m.params?.payload === "string" &&
        m.params.payload.startsWith("BARRIER:"),
    );
    expect(barrierIdx, "BARRIER bindingCalled emitted").toBeGreaterThanOrEqual(
      0,
    );

    const watermark = JSON.parse(
      messages[barrierIdx].params.payload.slice("BARRIER:".length),
    ).watermark;
    expect(typeof watermark, "watermark is number").toBe("number");
    expect(watermark, "watermark > 0").toBeGreaterThan(0);

    // Assertion 2 (the point): the RR whose body the page consumed
    // (n == watermark) appears at a strictly earlier JSONL index than
    // BARRIER. Names the missing response if it fails.
    let watermarkIdx = -1;
    for (let i = 0; i < barrierIdx; i++) {
      const e = messages[i];
      if (e.method !== "Network.responseReceived") continue;
      if (!(e.params?.response?.url ?? "").includes("/payload")) continue;
      const r = e.params.response;
      if (r.body == null) continue;
      const text =
        r.encoding === "base64"
          ? Buffer.from(r.body, "base64").toString("utf8")
          : r.body;
      const body = JSON.parse(text);
      if (body.n === watermark) {
        watermarkIdx = i;
        break;
      }
    }
    expect(
      watermarkIdx,
      `RR with body.n=${watermark} precedes BARRIER (idx ${barrierIdx})`,
    ).toBeGreaterThanOrEqual(0);

    // Assertion 3: BARRIER emitted exactly once. The page emits the
    // mark a single time after the await; a second emission would
    // indicate capture double-emitted the bindingCalled.
    const barriers = messages.filter(
      (m) =>
        m.method === "Runtime.bindingCalled" &&
        m.params?.name === "harBrowseMark" &&
        typeof m.params?.payload === "string" &&
        m.params.payload.startsWith("BARRIER:"),
    );
    expect(barriers.length, "BARRIER emitted exactly once").toBe(1);

    // Assertion 5 + 6: adversarial regime bounds. Both metrics should
    // be much smaller than N — watermark = max n consumed by the
    // renderer at BARRIER time; rrBefore = /payload RRs the session
    // already processed by BARRIER time. If either exceeds N/2, the
    // test has collapsed into barrier_smoke's all-form regime and the
    // subset invariant under test wasn't exercised. Warn earlier
    // (at N/4 and N/10) to surface regressions before they hard-fail.
    const rrsBefore = messages
      .slice(0, barrierIdx)
      .filter(
        (m) =>
          m.method === "Network.responseReceived" &&
          (m.params?.response?.url ?? "").includes("/payload"),
      ).length;
    bound(
      { name: "watermark", value: watermark, warnAt: N / 4, failAt: N / 2 },
      testInfo,
    );
    bound(
      { name: "rrBefore", value: rrsBefore, warnAt: N / 10, failAt: N / 5 },
      testInfo,
    );

    // Assertion 4: no duplicates in captured n values. Server's
    // payloadCount is monotonic + unique, so duplicates would indicate
    // double-emission of an RR in the capture pipeline.
    const ns = messages
      .filter(
        (m) =>
          m.method === "Network.responseReceived" &&
          (m.params?.response?.url ?? "").includes("/payload"),
      )
      .map((m) => {
        const r = m.params.response;
        if (r.body == null) return null;
        const text =
          r.encoding === "base64"
            ? Buffer.from(r.body, "base64").toString("utf8")
            : r.body;
        return JSON.parse(text).n;
      })
      .filter((n) => n != null);
    expect(new Set(ns).size, "captured n values unique").toBe(ns.length);
  } finally {
    await server.close();
  }
});
