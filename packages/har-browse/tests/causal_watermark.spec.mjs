/**
 * Causal-watermark adversarial oracle.
 *
 * Page-side, every consumed response appends its `body.n` (space-
 * delimited) to a `<div id="high-water-mark">`. At BARRIER time the
 * marker payload carries the current div contents — the page's
 * committed list of "responses I have consumed." Under adversarial
 * concurrency (most fetches still in flight at marker emit time),
 * every entry in that list must have a `Network.responseReceived`
 * earlier in the JSONL than BARRIER. Subset-of-events form: only the
 * consumed RRs need to precede; the rest may emit after.
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
        const div = document.createElement("div");
        div.id = "high-water-mark";
        document.body.appendChild(div);
        const all = [];
        for (let i = 0; i < n; i++) {
          all.push(
            fetch(`/payload?id=${i}`)
              .then((r) => r.json())
              .then(({ n: rn }) => {
                div.appendChild(document.createTextNode(rn + " "));
              }),
          );
        }
        // Wait for the first 1% to settle so the list is non-empty,
        // then snapshot it into BARRIER. The remaining ~99% stay in
        // flight — that's the adversarial condition under test.
        await Promise.all(all.slice(0, awaitCount));
        const consumed = div.textContent
          .trim()
          .split(/\s+/)
          .filter(Boolean)
          .map(Number);
        window.harBrowseMark("BARRIER:" + JSON.stringify({ consumed }));
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

    const consumed = JSON.parse(
      messages[barrierIdx].params.payload.slice("BARRIER:".length),
    ).consumed;
    expect(Array.isArray(consumed), "consumed is array").toBe(true);
    expect(consumed.length, "consumed not empty").toBeGreaterThan(0);

    // Assertion 2 (the point): every RR whose body the page consumed
    // (body.n in `consumed`) appears at a strictly earlier JSONL index
    // than BARRIER. Names the missing ones if it fails.
    const seenBefore = new Set();
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
      seenBefore.add(JSON.parse(text).n);
    }
    const missing = consumed.filter((n) => !seenBefore.has(n));
    expect(
      missing,
      `consumed RRs precede BARRIER (idx ${barrierIdx})`,
    ).toEqual([]);

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
    // be much smaller than N — consumed.length = responses the renderer
    // has actually observed at BARRIER time; rrBefore = /payload RRs
    // the session already processed by BARRIER time. If either exceeds
    // N/2, the test has collapsed into barrier_smoke's all-form regime
    // and the subset invariant under test wasn't exercised. Warn
    // earlier (at N/4 and N/10) to surface regressions before they
    // hard-fail.
    const rrsBefore = messages
      .slice(0, barrierIdx)
      .filter(
        (m) =>
          m.method === "Network.responseReceived" &&
          (m.params?.response?.url ?? "").includes("/payload"),
      ).length;
    bound(
      { name: "consumed", value: consumed.length, warnAt: N / 4, failAt: N / 2 },
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

    // Assertion 7: no extras. Every captured /payload n is in
    // [1, served]. Combined with A4 (uniqueness), this forces every
    // captured n to be a real served one — closes synthetic
    // post-BARRIER RR injection. Full completeness (captured ⊇ served)
    // is NOT asserted here: this test's adversarial regime closes
    // capture while ~99% of fetches are in flight, and those late
    // responses legitimately drop. barrier_smoke covers the quiescent
    // complete-form invariant.
    const served = server.requestLog.filter(
      (r) => r.pathname === "/payload",
    ).length;
    for (const n of ns) {
      expect(
        Number.isInteger(n) && n >= 1 && n <= served,
        `captured n=${n} in [1, ${served}]`,
      ).toBe(true);
    }

    // Assertion 8: body integrity. Every captured /payload body's `id`
    // (page→server→capture round-trip) matches the URL's id param.
    // Catches body corruption / truncation that preserves `n` but
    // strips or alters other fields.
    for (const m of messages) {
      if (m.method !== "Network.responseReceived") continue;
      const r = m.params?.response;
      if (!r || !(r.url ?? "").includes("/payload") || r.body == null) continue;
      const text =
        r.encoding === "base64"
          ? Buffer.from(r.body, "base64").toString("utf8")
          : r.body;
      const body = JSON.parse(text);
      const urlId = new URL(r.url).searchParams.get("id");
      expect(body.id, `body.id round-trips for n=${body.n}`).toBe(urlId);
    }
  } finally {
    await server.close();
  }
});
